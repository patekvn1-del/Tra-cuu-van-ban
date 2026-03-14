import re
import logging
import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from config import SOAP_URL, SOAP_NAMESPACE, VBPL_BASE, VBPL_DOMAIN, HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

def _call_soap(action, body_xml):
    envelope = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>{}</soap:Body>
</soap:Envelope>""".format(body_xml)
    headers_soap = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "{}{}".format(SOAP_NAMESPACE, action),
    }
    try:
        resp = requests.post(SOAP_URL, data=envelope.encode("utf-8"),
                             headers=headers_soap, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as e:
        logger.error("[SOAP] {} loi: {}".format(action, e))
        return None

def _find_text(el, tag):
    found = el.find(".//" + tag)
    if found is None:
        for child in el.iter():
            if child.tag.split("}")[-1] == tag:
                return (child.text or "").strip()
    return (found.text or "").strip() if found is not None else ""

def tim_kiem_soap(so_ky_hieu):
    body = """<GetListVanBanByListSKH xmlns="{}">
      <strListSKH>{}</strListSKH>
    </GetListVanBanByListSKH>""".format(SOAP_NAMESPACE, so_ky_hieu)
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
                "id": vb_id,
                "ten": _find_text(item, "Title") or _find_text(item, "TenVanBan"),
                "so_ky_hieu": _find_text(item, "SoKyHieu") or so_ky_hieu,
                "ngay_ban_hanh": _find_text(item, "NgayBanHanh"),
                "co_quan_ban_hanh": _find_text(item, "CoQuanBanHanh"),
                "trang_thai": _find_text(item, "TrangThai") or _find_text(item, "HieuLuc"),
                "loai_van_ban": _find_text(item, "LoaiVanBan"),
                "url": "{}/TW/Pages/vbpq-van-ban.aspx?ItemID={}".format(VBPL_BASE, vb_id),
            })
    return results

def lay_chi_tiet_soap(vb_id):
    body = """<GetVanBanById xmlns="{}">
      <iID>{}</iID>
    </GetVanBanById>""".format(SOAP_NAMESPACE, vb_id)
    root = _call_soap("GetVanBanById", body)
    if root is None:
        return {}
    return {
        "ten": _find_text(root, "Title") or _find_text(root, "TenVanBan"),
        "so_ky_hieu": _find_text(root, "SoKyHieu"),
        "ngay_ban_hanh": _find_text(root, "NgayBanHanh"),
        "co_quan_ban_hanh": _find_text(root, "CoQuanBanHanh"),
        "loai_van_ban": _find_text(root, "LoaiVanBan"),
        "trang_thai": _find_text(root, "TrangThai") or _find_text(root, "HieuLuc"),
        "ngay_hieu_luc": _find_text(root, "NgayHieuLuc"),
        "trich_yeu": _find_text(root, "TrichYeu"),
    }

def lay_van_ban_tac_dong(vb_id):
    body = """<GetLichSuVB xmlns="{}">
      <iID>{}</iID>
    </GetLichSuVB>""".format(SOAP_NAMESPACE, vb_id)
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
            "ten": ten,
            "so_ky_hieu": _find_text(item, "SoKyHieu"),
            "loai_tac_dong": _find_text(item, "LoaiTacDong") or "Tac dong",
            "url": "{}/TW/Pages/vbpq-van-ban.aspx?ItemID={}".format(VBPL_BASE, lic_id) if lic_id else "",
        })
    return ket_qua

def lay_file_dinh_kem(vb_id):
    body = """<GetListAttach xmlns="{}">
      <iID>{}</iID>
    </GetListAttach>""".format(SOAP_NAMESPACE, vb_id)
    root = _call_soap("GetListAttach", body)
    if root is None:
        return []
    files = []
    for item in root.iter():
        url = _find_text(item, "Url") or _find_text(item, "FileUrl")
        if url and any(ext in url.lower() for ext in [".pdf", ".doc", ".docx"]):
            ten = _find_text(item, "FileName") or _find_text(item, "Title") or "Tai file"
            files.append({
                "ten": ten,
                "url": url if url.startswith("http") else "{}{}".format(VBPL_BASE, url),
                "loai": url.rsplit(".", 1)[-1].upper(),
            })
    return files

def tim_kiem_web(so_ky_hieu,
import re
import logging
import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from config import SOAP_URL, SOAP_NAMESPACE, VBPL_BASE, VBPL_DOMAIN, HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

def _call_soap(action, body_xml):
    envelope = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>{}</soap:Body>
</soap:Envelope>""".format(body_xml)
    headers_soap = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "{}{}".format(SOAP_NAMESPACE, action),
    }
    try:
        resp = requests.post(SOAP_URL, data=envelope.encode("utf-8"),
                             headers=headers_soap, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as e:
        logger.error("[SOAP] {} loi: {}".format(action, e))
        return None

def _find_text(el, tag):
    found = el.find(".//" + tag)
    if found is None:
        for child in el.iter():
            if child.tag.split("}")[-1] == tag:
                return (child.text or "").strip()
    return (found.text or "").strip() if found is not None else ""

def tim_kiem_soap(so_ky_hieu):
    body = """<GetListVanBanByListSKH xmlns="{}">
      <strListSKH>{}</strListSKH>
    </GetListVanBanByListSKH>""".format(SOAP_NAMESPACE, so_ky_hieu)
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
                "id": vb_id,
                "ten": _find_text(item, "Title") or _find_text(item, "TenVanBan"),
                "so_ky_hieu": _find_text(item, "SoKyHieu") or so_ky_hieu,
                "ngay_ban_hanh": _find_text(item, "NgayBanHanh"),
                "co_quan_ban_hanh": _find_text(item, "CoQuanBanHanh"),
                "trang_thai": _find_text(item, "TrangThai") or _find_text(item, "HieuLuc"),
                "loai_van_ban": _find_text(item, "LoaiVanBan"),
                "url": "{}/TW/Pages/vbpq-van-ban.aspx?ItemID={}".format(VBPL_BASE, vb_id),
            })
    return results

def lay_chi_tiet_soap(vb_id):
    body = """<GetVanBanById xmlns="{}">
      <iID>{}</iID>
    </GetVanBanById>""".format(SOAP_NAMESPACE, vb_id)
    root = _call_soap("GetVanBanById", body)
    if root is None:
        return {}
    return {
        "ten": _find_text(root, "Title") or _find_text(root, "TenVanBan"),
        "so_ky_hieu": _find_text(root, "SoKyHieu"),
        "ngay_ban_hanh": _find_text(root, "NgayBanHanh"),
        "co_quan_ban_hanh": _find_text(root, "CoQuanBanHanh"),
        "loai_van_ban": _find_text(root, "LoaiVanBan"),
        "trang_thai": _find_text(root, "TrangThai") or _find_text(root, "HieuLuc"),
        "ngay_hieu_luc": _find_text(root, "NgayHieuLuc"),
        "trich_yeu": _find_text(root, "TrichYeu"),
    }

def lay_van_ban_tac_dong(vb_id):
    body = """<GetLichSuVB xmlns="{}">
      <iID>{}</iID>
    </GetLichSuVB>""".format(SOAP_NAMESPACE, vb_id)
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
            "ten": ten,
            "so_ky_hieu": _find_text(item, "SoKyHieu"),
            "loai_tac_dong": _find_text(item, "LoaiTacDong") or "Tac dong",
            "url": "{}/TW/Pages/vbpq-van-ban.aspx?ItemID={}".format(VBPL_BASE, lic_id) if lic_id else "",
        })
    return ket_qua

def lay_file_dinh_kem(vb_id):
    body = """<GetListAttach xmlns="{}">
      <iID>{}</iID>
    </GetListAttach>""".format(SOAP_NAMESPACE, vb_id)
    root = _call_soap("GetListAttach", body)
    if root is None:
        return []
    files = []
    for item in root.iter():
        url = _find_text(item, "Url") or _find_text(item, "FileUrl")
        if url and any(ext in url.lower() for ext in [".pdf", ".doc", ".docx"]):
            ten = _find_text(item, "FileName") or _find_text(item, "Title") or "Tai file"
            files.append({
                "ten": ten,
                "url": url if url.startswith("http") else "{}{}".format(VBPL_BASE, url),
                "loai": url.rsplit(".", 1)[-1].upper(),
            })
    return files

def tim_kiem_web(so_ky_hieu,
