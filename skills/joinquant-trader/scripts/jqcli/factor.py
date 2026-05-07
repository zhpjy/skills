from __future__ import annotations

import json
from typing import Any


class FactorService:
    def __init__(self, http_client):
        self.http_client = http_client

    def get_settings(self) -> dict[str, Any]:
        return _data(self.http_client.get("/factorlib/index/getSetting").text)

    def list_categories(self) -> dict[str, Any]:
        categories = _data(self.http_client.get("/factorlib/index/getFctCategoryList").text)
        return {"categories": categories, "count": len(categories) if isinstance(categories, list) else None}

    def list_factors(
        self,
        *,
        category_id: str = "0",
        universe_type: str | None = None,
        time_range: str | None = None,
        commision_fee: str | None = None,
        skip_paused: str | None = None,
    ) -> dict[str, Any]:
        params = _clean_params(
            {
                "categoryId": category_id,
                "universeType": universe_type,
                "timeRange": time_range,
                "commisionFee": commision_fee,
                "skipPaused": skip_paused,
            }
        )
        factors = _data(self.http_client.get("/factorlib/index/getList", params=params).text)
        return {"factors": factors, "count": len(factors) if isinstance(factors, list) else None}

    def get_info(self, factor_id: str) -> dict[str, Any]:
        return _data(
            self.http_client.get(
                "/factorlib/index/getInfo",
                params={"id": factor_id, "isFactorShare": "0"},
            ).text
        )

    def get_performance(
        self,
        *,
        factor_id: str,
        universe_type: str,
        time_range: str,
        commision_fee: str,
        skip_paused: str,
        turnover_period: str | None = None,
        delay: str | None = None,
        turnover_time: str | None = None,
    ) -> dict[str, Any]:
        return _data(
            self.http_client.get(
                "/factorlib/index/getPerformance",
                params=self._analysis_params(
                    factor_id=factor_id,
                    universe_type=universe_type,
                    time_range=time_range,
                    commision_fee=commision_fee,
                    skip_paused=skip_paused,
                    turnover_period=turnover_period,
                    delay=delay,
                    turnover_time=turnover_time,
                ),
            ).text
        )

    def get_daily_stats(
        self,
        *,
        factor_id: str,
        side: str,
        universe_type: str,
        time_range: str,
        commision_fee: str,
        skip_paused: str,
        turnover_period: str | None = None,
        delay: str | None = None,
        turnover_time: str | None = None,
    ) -> Any:
        return _data(
            self.http_client.get(
                "/factorlib/index/getDailyStats",
                params={
                    **self._analysis_params(
                        factor_id=factor_id,
                        universe_type=universe_type,
                        time_range=time_range,
                        commision_fee=commision_fee,
                        skip_paused=skip_paused,
                        turnover_period=turnover_period,
                        delay=delay,
                        turnover_time=turnover_time,
                    ),
                    "side": side,
                },
            ).text
        )

    def get_ic(
        self,
        *,
        factor_id: str,
        universe_type: str,
        time_range: str,
        skip_paused: str,
        turnover_period: str | None = None,
        delay: str | None = None,
        turnover_time: str | None = None,
    ) -> dict[str, Any]:
        return _data(
            self.http_client.get(
                "/factorlib/index/getIC",
                params=self._analysis_params(
                    factor_id=factor_id,
                    universe_type=universe_type,
                    time_range=time_range,
                    skip_paused=skip_paused,
                    turnover_period=turnover_period,
                    delay=delay,
                    turnover_time=turnover_time,
                ),
            ).text
        )

    def get_turnovers(
        self,
        *,
        factor_id: str,
        side: str,
        universe_type: str,
        time_range: str,
        commision_fee: str,
        skip_paused: str,
        turnover_period: str | None = None,
        delay: str | None = None,
        turnover_time: str | None = None,
    ) -> dict[str, Any]:
        return _data(
            self.http_client.get(
                "/factorlib/index/getTurnovers",
                params={
                    **self._analysis_params(
                        factor_id=factor_id,
                        universe_type=universe_type,
                        time_range=time_range,
                        commision_fee=commision_fee,
                        skip_paused=skip_paused,
                        turnover_period=turnover_period,
                        delay=delay,
                        turnover_time=turnover_time,
                    ),
                    "side": side,
                },
            ).text
        )

    def get_stock_list(self, *, factor_id: str, universe_type: str) -> dict[str, Any]:
        return _data(
            self.http_client.get(
                "/factorlib/index/getFactorStockList",
                params={"id": factor_id, "universeType": universe_type, "isFactorShare": "0"},
            ).text
        )

    def get_detail(
        self,
        *,
        factor_id: str,
        universe_type: str,
        time_range: str,
        commision_fee: str,
        skip_paused: str,
        side: str = "long",
        turnover_period: str | None = None,
        delay: str | None = None,
        turnover_time: str | None = None,
        include_series: bool = False,
    ) -> dict[str, Any]:
        detail = {
            "id": factor_id,
            "filters": {
                "universe_type": universe_type,
                "time_range": time_range,
                "commision_fee": commision_fee,
                "skip_paused": skip_paused,
                "side": side,
                "turnover_period": turnover_period,
                "delay": delay,
                "turnover_time": turnover_time,
            },
            "info": self.get_info(factor_id),
            "performance": self.get_performance(
                factor_id=factor_id,
                universe_type=universe_type,
                time_range=time_range,
                commision_fee=commision_fee,
                skip_paused=skip_paused,
                turnover_period=turnover_period,
                delay=delay,
                turnover_time=turnover_time,
            ),
            "stock_list": self.get_stock_list(factor_id=factor_id, universe_type=universe_type),
        }
        if include_series:
            detail["daily_stats"] = self.get_daily_stats(
                factor_id=factor_id,
                side=side,
                universe_type=universe_type,
                time_range=time_range,
                commision_fee=commision_fee,
                skip_paused=skip_paused,
                turnover_period=turnover_period,
                delay=delay,
                turnover_time=turnover_time,
            )
            detail["ic"] = self.get_ic(
                factor_id=factor_id,
                universe_type=universe_type,
                time_range=time_range,
                skip_paused=skip_paused,
                turnover_period=turnover_period,
                delay=delay,
                turnover_time=turnover_time,
            )
            detail["turnovers"] = self.get_turnovers(
                factor_id=factor_id,
                side=side,
                universe_type=universe_type,
                time_range=time_range,
                commision_fee=commision_fee,
                skip_paused=skip_paused,
                turnover_period=turnover_period,
                delay=delay,
                turnover_time=turnover_time,
            )
        return detail

    def _analysis_params(
        self,
        *,
        factor_id: str,
        universe_type: str,
        time_range: str,
        skip_paused: str,
        commision_fee: str | None = None,
        turnover_period: str | None = None,
        delay: str | None = None,
        turnover_time: str | None = None,
    ) -> dict[str, str]:
        return _clean_params(
            {
                "id": factor_id,
                "universeType": universe_type,
                "timeRange": time_range,
                "commisionFee": commision_fee,
                "skipPaused": skip_paused,
                "turnoverPeriod": turnover_period,
                "delay": delay,
                "turnoverTime": turnover_time,
                "isFactorShare": "0",
            }
        )


def _data(text: str) -> Any:
    parsed = _json_or_text(text)
    if isinstance(parsed, dict) and "data" in parsed:
        return parsed["data"]
    return parsed


def _json_or_text(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _clean_params(params: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in params.items() if value not in (None, "")}
