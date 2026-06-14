"""
Backend central (siège) — agrège les données des backends pays en parallèle.
Mode dégradé natif : si un pays est indisponible, les autres restent accessibles.
"""
import asyncio
import os
from typing import Any

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FutureKawa — Backend Central", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

COUNTRY_URLS: dict[str, str] = {
    "BR": os.getenv("URL_BR", "http://api-br:8000"),
    "EC": os.getenv("URL_EC", "http://api-ec:8000"),
    "CO": os.getenv("URL_CO", "http://api-co:8000"),
}

TIMEOUT = httpx.Timeout(10.0)


async def fetch(client: httpx.AsyncClient, country: str, path: str) -> tuple[str, Any, bool]:
    url = COUNTRY_URLS[country] + path
    try:
        resp = await client.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return country, resp.json(), False
    except Exception:
        return country, None, True


@app.get("/health")
async def health():
    return {"status": "ok", "service": "central"}


@app.get("/dashboard/summary")
async def dashboard_summary():
    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, c, "/dashboard/summary") for c in COUNTRY_URLS]
        results = await asyncio.gather(*tasks)

    degraded_countries = []
    countries_data = []
    totals = {
        "total_lots": 0,
        "lots_conformes": 0,
        "lots_en_alerte": 0,
        "lots_perimes": 0,
        "active_alerts": 0,
    }

    for country, data, failed in results:
        if failed:
            degraded_countries.append(country)
        else:
            countries_data.append(data)
            for key in totals:
                totals[key] += data.get(key, 0)

    return {
        **totals,
        "degraded_countries": degraded_countries,
        "countries": countries_data,
    }


@app.get("/countries/{country}/lots")
async def country_lots(
    country: str,
    status: str | None = Query(None),
    warehouse_id: int | None = Query(None),
):
    country = country.upper()
    if country not in COUNTRY_URLS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pays inconnu")
    params: dict[str, Any] = {}
    if status:
        params["status"] = status
    if warehouse_id:
        params["warehouse_id"] = warehouse_id
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                COUNTRY_URLS[country] + "/lots/",
                params=params,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=f"Backend {country} indisponible") from exc


@app.get("/countries/{country}/lots/{lot_id}")
async def country_lot_detail(country: str, lot_id: str):
    country = country.upper()
    if country not in COUNTRY_URLS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pays inconnu")
    async with httpx.AsyncClient() as client:
        try:
            lot_resp = await client.get(
                COUNTRY_URLS[country] + f"/lots/{lot_id}", timeout=TIMEOUT
            )
            lot_resp.raise_for_status()
            lot = lot_resp.json()
            measures_resp = await client.get(
                COUNTRY_URLS[country] + "/measurements/",
                params={"lot_id": lot_id, "limit": 500},
                timeout=TIMEOUT,
            )
            measures_resp.raise_for_status()
            return {**lot, "measurements": measures_resp.json()}
        except Exception as exc:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=f"Backend {country} indisponible") from exc


@app.get("/countries/{country}/warehouses")
async def country_warehouses(country: str):
    country = country.upper()
    if country not in COUNTRY_URLS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pays inconnu")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(COUNTRY_URLS[country] + "/warehouses/", timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=f"Backend {country} indisponible") from exc


@app.get("/alerts")
async def all_alerts(
    active_only: bool = Query(False),
    severity: str | None = Query(None),
    alert_type: str | None = Query(None),
):
    params: dict[str, Any] = {}
    if active_only:
        params["active_only"] = "true"
    if severity:
        params["severity"] = severity
    if alert_type:
        params["alert_type"] = alert_type

    async with httpx.AsyncClient() as client:
        tasks = [fetch(client, c, f"/alerts/?{'&'.join(f'{k}={v}' for k,v in params.items())}") for c in COUNTRY_URLS]
        results = await asyncio.gather(*tasks)

    all_alert_list = []
    degraded = []
    for country, data, failed in results:
        if failed:
            degraded.append(country)
        elif data:
            for alert in data:
                alert["country"] = country
            all_alert_list.extend(data)

    all_alert_list.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    return {"alerts": all_alert_list, "degraded_countries": degraded}


@app.post("/countries/{country}/alerts/{alert_id}/resolve")
async def resolve_alert(country: str, alert_id: int):
    country = country.upper()
    if country not in COUNTRY_URLS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pays inconnu")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                COUNTRY_URLS[country] + f"/alerts/{alert_id}/resolve", timeout=TIMEOUT
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail=str(exc)) from exc
