import re
import logging
import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from config import SOAP_URL, SOAP_NAMESPACE, VBPL_BASE, VBPL_DOMAIN, HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

def _call_soap(action, body_xml):
    envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>{body_xml}</soap:Body>
</soap:Envelope>"""
    headers_soap = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": f"{SOAP_NAMESPACE}{action}",
    }
    try:
        resp = requests.post(SOAP_URL, data=envelope.encode("utf-8"),
                             headers=headers_soap, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as e:
        logger.error(f"[SOAP] {action} lỗi: {e}")
        return None

def _find_text(el, tag):
    found = el.find(f".//{tag}")
    if found is None:
        for child in el.iter():
            if child.tag.split("}")[-1] == tag:
                return (child.text or "").strip()
    return (found.text or "").strip() if found is not None else ""

def tim_kiem_soap(so_ky_hieu):
    body = f"""<GetListVanBanByListSKH xmlns="{SOAP_NAMESPACE}">
      <strListSKH>{so_ky_hieu}</strListSKH>
    </GetListVanBanByListSKH>"""
    root = _call_soap("GetListVanBanByListSKH", body)
    if root is None:
        return []
    results = []
    for item in root.iter():
        tag_local = item.tag.split("}")[-1]
        if "Item" in tag_local or "VanBan" in tag_local:
            vb_id = _find_text(item, "ID") or _find_text(item, "Id")
            if not vb_id:
                continue
            results.append({
                "id":              vb_id,
                "ten":             _find_text(item, "Title") or _find_text(item, "TenVanBan"),
                "so_ky_hieu":      _find_text(item, "SoKyHieu") or so_ky_hieu,
                "ngay_ban_hanh":   _find_text(item, "NgayBanHanh"),
                "co_quan_ban_hanh":_find_text(item, "CoQuanBanHanh"),
                "trang_thai":      _find_text(item, "TrangThai") or _find_text(item, "HieuLuc"),
                "loai_van_ban":    _find_text(item, "LoaiVanBan"),
                "url": f"{VBPL_BASE}/TW/Pages/vbpq-van-ban.aspx?ItemID={vb_id}",
            })
    return results

def lay_chi_tiet_soap(vb_id):
    body = f"""<GetVanBanById xmlns="{SOAP_NAMESPACE}">
      <iID>{vb_id}</iID>
    </GetVanBanById>"""
    root = _call_soap("GetVanBanById", body)
    if root is None:
        return {}
    return {
        "ten":              _find_text(root, "Title") or _find_text(root, "TenVanBan"),
        "so_ky_hieu":       _find_text(root, "SoKyHieu"),
        "ngay_ban_hanh":    _find_text(root, "NgayBanHanh"),
        "co_quan_ban_hanh": _find_text(root, "CoQuanBanHanh"),
        "loai_van_ban":     _find_text(root, "LoaiVanBan"),
        "trang_thai":       _find_text(root, "TrangThai") or _find_text(root, "HieuLuc"),
        "ngay_hieu_luc":    _find_text(root, "NgayHieuLuc"),
        "trich_yeu":        _find_text(root, "TrichYeu"),
    }

def lay_van_ban_tac_dong(vb_id):
    body = f"""<GetLichSuVB xmlns="{SOAP_NAMESPACE}">
      <iID>{vb_id}</iID>
    </GetLichSuVB>"""
    root = _call_soap("GetLichSuVB", body)
    if root is None:
        return []
    ket_qua = []
    for item in root.iter():
        ten = _find_text(item, "TenVanBan") or _find_text(item, "Title")
        if not ten:
            continue
        lic_id = _find_text(item, "ID") or _find_text(item, "Id")
        ket_qua.append({
            "ten":           ten,
            "so_ky_hieu":    _find_text(item, "SoKyHieu"),
            "loai_tac_dong": _find_text(item, "LoaiTacDong") or "Tác động",
            "url": f"{VBPL_BASE}/TW/Pages/vbpq-van-ban.aspx?ItemID={lic_id}" if lic_id else "",
        })
    return ket_qua

def lay_file_dinh_kem(vb_id):
    body = f"""<GetListAttach xmlns="{SOAP_NAMESPACE}">
      <iID>{vb_id}</iID>
    </GetListAttach>"""
    root = _call_soap("GetListAttach", body)
    if root is None:
        return []
    files = []
    for item in root.iter():
        url = _find_text(item, "Url") or _find_text(item, "FileUrl")
        if url and any(ext in url.lower() for ext in [".pdf", ".doc", ".docx"]):
            ten = _find_text(item, "FileName") or _find_text(item, "Title") or "Tải file"
            files.append({
                "ten":  ten,
                "url":  url if url.startswith("http") else f"{VBPL_BASE}{url}",
                "loai": url.rsplit(".", 1)[-1].upper(),
            })
    return files

def tim_kiem_web(so_ky_hieu, dia_phuong="tphcm"):
    base   = VBPL_DOMAIN.get(dia_phuong, f"{VBPL_BASE}/{dia_phuong}")
    url    = f"{base}/Pages/vbpq-tim-kiem.aspx"
    params = {"s": "1", "Keyword": so_ky_hieu}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        for sel in [".list-vbpq-result .row-item", ".vbpq-item",
                    "ul.list-vbpq > li", ".search-result-item"]:
            items = soup.select(sel)
            if items:
                break
        results = []
        for item in items[:5]:
            link = item.select_one("a.title, h3 > a, a[href*='ItemID']")
            if not link:
                continue
            href      = link.get("href", "")
            id_match  = re.search(r"ItemID=(\d+)", href, re.I)
            tt_el     = item.select_one(".trang-thai, .hieu-luc, span[class*='hieu']")
            results.append({
                "id":         id_match.group(1) if id_match else None,
                "ten":        link.get_text(strip=True),
                "so_ky_hieu": so_ky_hieu,
                "trang_thai": tt_el.get_text(strip=True) if tt_el else "",
                "url":        href if href.startswith("http") else f"{base}{href}",
            })
        return results
    except Exception as e:
        logger.error(f"[WEB] Scraping lỗi: {e}")
        return []

def lay_chi_tiet_web(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.encoding = "utf-8"
        soup   = BeautifulSoup(resp.text, "lxml")
        detail = {}
        for sel in ["h1.title-vb", ".title-main", "h1"]:
            el = soup.select_one(sel)
            if el:
                detail["ten"] = el.get_text(strip=True)
                break
        for row in soup.select(".table-info tr, .vbpq-info tr, table tr"):
            cells = row.select("td, th")
            if len(cells) < 2:
                continue
            key = cells[0].get_text(strip=True).lower()
            val = cells[1].get_text(strip=True)
            if "số ký hiệu"      in key: detail["so_ky_hieu"]       = val
            elif "ngày ban hành" in key: detail["ngay_ban_hanh"]     = val
            elif "cơ quan"       in key: detail["co_quan_ban_hanh"]  = val
            elif "hiệu lực"      in key: detail["ngay_hieu_luc"]     = val
            elif "trạng thái"    in key: detail["trang_thai"]        = val
            elif "loại văn bản"  in key: detail["loai_van_ban"]      = val
        files = []
        for a in soup.select('a[href$=".pdf"], a[href$=".doc"], a[href$=".docx"]'):
            href = a.get("href", "")
            files.append({
                "ten":  a.get_text(strip=True) or "Tải file",
                "url":  href if href.startswith("http") else f"{VBPL_BASE}{href}",
                "loai": href.rsplit(".", 1)[-1].upper(),
            })
        detail["files"] = files
        vb_td = []
        for section in soup.select(".van-ban-het-hieu-luc, .vb-bi-thay-the"):
            for a in section.select("a")[:5]:
                vb_td.append({"ten": a.get_text(strip=True),
                              "url": a.get("href", ""),
                              "loai_tac_dong": "Thay thế / Bãi bỏ"})
        detail["van_ban_tac_dong"] = vb_td
        return detail
    except Exception as e:
        logger.error(f"[WEB] Chi tiết lỗi: {e}")
        return {}

def tra_cuu_van_ban(so_ky_hieu, dia_phuong="tphcm"):
    results = tim_kiem_soap(so_ky_hieu)
    if not results:
        logger.info("[API] SOAP rỗng → web scraping...")
        results = tim_kiem_web(so_ky_hieu, dia_phuong)
    enriched = []
    for r in results[:3]:
        vb_id = r.get("id")
        if vb_id:
            detail = lay_chi_tiet_soap(vb_id)
            r.update({k: v for k, v in detail.items() if v})
            r["files"]            = lay_file_dinh_kem(vb_id)
            r["van_ban_tac_dong"] = lay_van_ban_tac_dong(vb_id)
        elif r.get("url"):
            web_detail = lay_chi_tiet_web(r["url"])
            r.update({k: v for k, v in web_detail.items() if v})
        enriched.append(r)
    return enriched

def xac_dinh_trang_thai(trang_thai):
    ts = trang_thai.lower()
    if any(x in ts for x in ["còn hiệu lực", "con hieu luc"]):
        return "✅", "CÒN HIỆU LỰC"
    if any(x in ts for x in ["một phần", "mot phan"]):
        return "⚠️", "HẾT HIỆU LỰC MỘT PHẦN"
    if any(x in ts for x in ["hết hiệu lực", "het hieu luc"]):
        return "❌", "HẾT HIỆU LỰC"
    if any(x in ts for x in ["chưa", "chua"]):
        return "🕐", "CHƯA CÓ HIỆU LỰC"
    return "❓", trang_thai or "Không xác định"
