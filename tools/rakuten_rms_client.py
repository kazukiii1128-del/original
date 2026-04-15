#!/usr/bin/env python3
"""
Minimal Rakuten RMS API client wrapper.

This is intentionally generic: fill `credentials/rakuten_rms_config.json` with your
RMS endpoints and auth details. Example config:

{
  "base_url": "https://api.rms.rakuten.co.jp",
  "auth": { "type": "header", "header_name": "Authorization", "value": "Bearer xxxxx" },
  "list_orders_url": "/shops/{shop_id}/orders",
  "update_order_url": "/shops/{shop_id}/orders/{order_id}/status",
  "default_params": {"limit":50}
}

Endpoints and param names vary by RMS setup — adapt the config accordingly.
"""
import json
import requests
import os
from typing import Any, Dict, List


class RakutenRMSClient:
    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"RMS config not found: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            self.cfg: Dict[str, Any] = json.load(f)
        self.base = self.cfg.get("base_url", "").rstrip("/")
        self.session = requests.Session()
        auth = self.cfg.get("auth") or {}
        if auth.get("type") == "header":
            self.session.headers.update({auth.get("header_name"): auth.get("value")})

    def _full_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base}{path}"

    def list_orders(self, shop_id: str = None, status: str = None, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        url_tmpl = self.cfg.get("list_orders_url")
        if not url_tmpl:
            raise ValueError("list_orders_url not set in config")
        url = url_tmpl.format(shop_id=shop_id or self.cfg.get("shop_id", ""))
        full = self._full_url(url)
        q = dict(self.cfg.get("default_params", {}))
        if params:
            q.update(params)
        if status:
            q[ self.cfg.get("status_param_name", "status") ] = status
        resp = self.session.get(full, params=q)
        resp.raise_for_status()
        data = resp.json()
        # Assume orders are in a top-level list or under a key specified in config
        orders_key = self.cfg.get("orders_key")
        if orders_key:
            return data.get(orders_key, [])
        if isinstance(data, list):
            return data
        # Try common keys
        for k in ("orders", "data", "result"):
            if k in data and isinstance(data[k], list):
                return data[k]
        # Fallback: return raw data wrapped
        return [data]

    def update_order_status(self, order_id: str, shop_id: str = None, payload: Dict[str, Any] = None, method: str = "post") -> Dict[str, Any]:
        url_tmpl = self.cfg.get("update_order_url")
        if not url_tmpl:
            raise ValueError("update_order_url not set in config")
        url = url_tmpl.format(order_id=order_id, shop_id=shop_id or self.cfg.get("shop_id", ""))
        full = self._full_url(url)
        data = payload or {}
        m = method.lower()
        if m == "post":
            resp = self.session.post(full, json=data)
        elif m == "put":
            resp = self.session.put(full, json=data)
        elif m == "patch":
            resp = self.session.patch(full, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status_code": resp.status_code}
