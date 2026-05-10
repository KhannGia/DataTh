from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Datathon 2026 - EDA Dashboard",
    page_icon="📊",
    layout="wide",
)

ROOT_DIR = Path(__file__).resolve().parent
SEED_DIR = ROOT_DIR / "seeds"
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}
CHART_HEIGHT = 380

PROMO_COLOR_MAP = {
    "No Promo": "#7D8597",
    "Single": "#2A9D8F",
    "Stacked": "#E76F51",
}
STOCKOUT_COLOR_MAP = {
    "No Stockout": "#94A3B8",
    "Stockout": "#DC2626",
}


def vnd_format(value: float) -> str:
    return f"{value:,.0f} VND"


def pct_format(value: float) -> str:
    if not np.isfinite(value):
        return "N/A"
    return f"{value * 100:.2f}%"


def format_rel_delta(current: float, previous: float) -> str | None:
    if not np.isfinite(previous) or np.isclose(previous, 0.0):
        return None
    delta = (current - previous) / abs(previous)
    return f"{delta:+.1%}"


def format_pp_delta(current: float, previous: float) -> str | None:
    if not np.isfinite(current) or not np.isfinite(previous):
        return None
    delta_pp = (current - previous) * 100
    return f"{delta_pp:+.2f} pp"


def normalize_date_range(
    value: tuple[datetime, datetime] | tuple | list | datetime,
) -> tuple[datetime, datetime]:
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return pd.Timestamp(value[0]), pd.Timestamp(value[1])
    one_date = pd.Timestamp(value)
    return one_date, one_date


def apply_date_preset(
    preset: str, min_date: datetime, max_date: datetime
) -> tuple[datetime, datetime]:
    min_ts = pd.Timestamp(min_date)
    max_ts = pd.Timestamp(max_date)
    if preset == "6 tháng gần nhất":
        start = max(min_ts, max_ts - pd.DateOffset(months=6))
        return start, max_ts
    if preset == "12 tháng gần nhất":
        start = max(min_ts, max_ts - pd.DateOffset(months=12))
        return start, max_ts
    return min_ts, max_ts


def split_current_previous(df: pd.DataFrame, date_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df, df

    unique_dates = pd.Series(df[date_col].dropna().unique()).sort_values().reset_index(drop=True)
    if len(unique_dates) < 2:
        return df, df.iloc[0:0]

    pivot = unique_dates.iloc[len(unique_dates) // 2]
    current = df[df[date_col] > pivot]
    previous = df[df[date_col] <= pivot]

    if current.empty or previous.empty:
        midpoint = len(df) // 2
        previous = df.iloc[:midpoint]
        current = df.iloc[midpoint:]
    return current, previous


def plot_chart(fig) -> None:
    fig.update_layout(
        height=CHART_HEIGHT,
        legend_title_text="",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def load_csv(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    path = SEED_DIR / f"{name}.csv"
    return pd.read_csv(path, parse_dates=parse_dates)


@st.cache_data(show_spinner=False)
def load_base_data() -> dict[str, pd.DataFrame]:
    return {
        "products": load_csv("products"),
        "customers": load_csv("customers", parse_dates=["signup_date"]),
        "promotions": load_csv("promotions", parse_dates=["start_date", "end_date"]),
        "orders": load_csv("orders", parse_dates=["order_date"]),
        "order_items": load_csv("order_items"),
        "returns": load_csv("returns", parse_dates=["return_date"]),
        "inventory": load_csv("inventory", parse_dates=["snapshot_date"]),
    }


def build_promo_mart(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    promo = (
        data["order_items"]
        .merge(
            data["orders"][["order_id", "order_date", "customer_id", "order_status"]],
            on="order_id",
            how="inner",
        )
        .merge(
            data["products"][["product_id", "category", "segment", "cogs"]],
            on="product_id",
            how="inner",
        )
        .merge(
            data["promotions"][["promo_id", "promo_name", "promo_type", "stackable_flag"]],
            on="promo_id",
            how="left",
        )
    )
    promo["gross_revenue"] = promo["unit_price"] * promo["quantity"]
    promo["net_revenue"] = promo["gross_revenue"] - promo["discount_amount"]
    promo["total_cogs"] = promo["cogs"] * promo["quantity"]
    promo["gross_profit"] = promo["net_revenue"] - promo["total_cogs"]
    promo["gross_margin_pct"] = np.where(
        promo["net_revenue"] > 0,
        promo["gross_profit"] / promo["net_revenue"],
        0,
    )
    promo["promo_status"] = np.select(
        [
            promo["promo_id"].notna() & promo["promo_id_2"].notna(),
            promo["promo_id"].notna(),
        ],
        ["Stacked", "Single"],
        default="No Promo",
    )
    promo["order_month"] = promo["order_date"].dt.to_period("M").dt.to_timestamp()
    return promo


def build_returns_mart(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    returns = (
        data["returns"]
        .merge(
            data["orders"][["order_id", "order_date", "customer_id", "order_source"]],
            on="order_id",
            how="left",
        )
        .merge(
            data["customers"][["customer_id", "gender", "age_group"]],
            on="customer_id",
            how="left",
        )
        .merge(
            data["products"][["product_id", "product_name", "category", "segment", "price"]],
            on="product_id",
            how="left",
        )
    )
    returns["days_to_return"] = (returns["return_date"] - returns["order_date"]).dt.days
    returns["return_month"] = returns["return_date"].dt.to_period("M").dt.to_timestamp()
    return returns


def build_inventory_mart(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    inventory = data["inventory"].merge(
        data["products"][["product_id", "price", "cogs"]],
        on="product_id",
        how="left",
    )
    days_in_month = inventory["snapshot_date"].dt.daysinmonth
    available_days = (days_in_month - inventory["stockout_days"]).clip(lower=0)
    inventory["avg_daily_sales_volume"] = np.where(
        available_days > 0,
        inventory["units_sold"] / available_days,
        0,
    )
    inventory["est_lost_revenue"] = (
        inventory["avg_daily_sales_volume"] * inventory["stockout_days"] * inventory["price"]
    )
    inventory["overstock_capital_value"] = np.where(
        inventory["overstock_flag"].astype(int) == 1,
        inventory["stock_on_hand"] * inventory["cogs"],
        0,
    )
    inventory["inventory_month"] = inventory["snapshot_date"].dt.to_period("M").dt.to_timestamp()
    return inventory


@st.cache_data(show_spinner=False)
def load_all_marts() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = load_base_data()
    return build_promo_mart(data), build_returns_mart(data), build_inventory_mart(data)


def main() -> None:
    st.title("📊 Datathon 2026 - EDA Dashboard")
    st.caption("VinTelligence | The Gridbreaker — Data Storytelling Workspace")

    promo, returns, inventory = load_all_marts()

    categories = sorted(
        set(promo["category"].dropna().unique())
        | set(returns["category"].dropna().unique())
        | set(inventory["category"].dropna().unique())
    )
    segments = sorted(
        set(promo["segment"].dropna().unique())
        | set(returns["segment"].dropna().unique())
        | set(inventory["segment"].dropna().unique())
    )

    promo_min_date = promo["order_date"].min()
    promo_max_date = promo["order_date"].max()
    inventory_min_date = inventory["snapshot_date"].min()
    inventory_max_date = inventory["snapshot_date"].max()
    preset_options = ["Toàn bộ dữ liệu", "12 tháng gần nhất", "6 tháng gần nhất"]

    if "selected_categories" not in st.session_state:
        st.session_state.selected_categories = categories.copy()
    if "selected_segments" not in st.session_state:
        st.session_state.selected_segments = segments.copy()
    if "top_n" not in st.session_state:
        st.session_state.top_n = 10
    if "promo_date_range" not in st.session_state:
        st.session_state.promo_date_range = (promo_min_date, promo_max_date)
    if "inventory_date_range" not in st.session_state:
        st.session_state.inventory_date_range = (inventory_min_date, inventory_max_date)
    if "date_preset" not in st.session_state:
        st.session_state.date_preset = preset_options[0]

    st.session_state.selected_categories = [
        c for c in st.session_state.selected_categories if c in categories
    ] or categories.copy()
    st.session_state.selected_segments = [
        s for s in st.session_state.selected_segments if s in segments
    ] or segments.copy()

    def reset_filters() -> None:
        st.session_state.selected_categories = categories.copy()
        st.session_state.selected_segments = segments.copy()
        st.session_state.top_n = 10
        st.session_state.promo_date_range = (promo_min_date, promo_max_date)
        st.session_state.inventory_date_range = (inventory_min_date, inventory_max_date)
        st.session_state.date_preset = preset_options[0]

    st.sidebar.header("Bộ lọc & điều khiển")
    st.sidebar.selectbox("Preset thời gian", preset_options, key="date_preset")

    if st.sidebar.button("Áp dụng preset thời gian", use_container_width=True):
        promo_start, promo_end = apply_date_preset(
            st.session_state.date_preset, promo_min_date, promo_max_date
        )
        inv_start, inv_end = apply_date_preset(
            st.session_state.date_preset, inventory_min_date, inventory_max_date
        )
        st.session_state.promo_date_range = (promo_start, promo_end)
        st.session_state.inventory_date_range = (inv_start, inv_end)

    st.sidebar.button("Reset filters", on_click=reset_filters, use_container_width=True)

    st.sidebar.multiselect("Category", categories, key="selected_categories")
    st.sidebar.multiselect("Segment", segments, key="selected_segments")
    st.sidebar.slider("Top N", min_value=5, max_value=25, key="top_n")
    st.sidebar.date_input(
        "Khoảng thời gian đơn hàng",
        min_value=promo_min_date,
        max_value=promo_max_date,
        key="promo_date_range",
    )
    st.sidebar.date_input(
        "Khoảng thời gian tồn kho",
        min_value=inventory_min_date,
        max_value=inventory_max_date,
        key="inventory_date_range",
    )

    selected_categories = st.session_state.selected_categories
    selected_segments = st.session_state.selected_segments
    top_n = st.session_state.top_n
    promo_start, promo_end = normalize_date_range(st.session_state.promo_date_range)
    inv_start, inv_end = normalize_date_range(st.session_state.inventory_date_range)

    promo_filtered = promo[
        promo["category"].isin(selected_categories)
        & promo["segment"].isin(selected_segments)
        & promo["order_date"].between(promo_start, promo_end)
    ].copy()
    returns_filtered = returns[
        returns["category"].isin(selected_categories)
        & returns["segment"].isin(selected_segments)
        & returns["order_date"].between(promo_start, promo_end)
    ].copy()
    inventory_filtered = inventory[
        inventory["category"].isin(selected_categories)
        & inventory["segment"].isin(selected_segments)
        & inventory["snapshot_date"].between(inv_start, inv_end)
    ].copy()

    if promo_filtered.empty and returns_filtered.empty and inventory_filtered.empty:
        st.warning("Không có dữ liệu cho bộ lọc hiện tại.")
        return

    seed_last_updated = max(
        datetime.fromtimestamp(path.stat().st_mtime)
        for path in SEED_DIR.glob("*.csv")
    )
    with st.container(border=True):
        i1, i2, i3 = st.columns(3)
        i1.metric("Last updated", seed_last_updated.strftime("%Y-%m-%d %H:%M"))
        i2.metric(
            "Rows after filtering",
            f"{len(promo_filtered) + len(returns_filtered) + len(inventory_filtered):,}",
        )
        i3.metric("Preset", st.session_state.date_preset)
        st.caption(
            f"Filter active: {len(selected_categories)}/{len(categories)} categories | "
            f"{len(selected_segments)}/{len(segments)} segments | Top N = {top_n}"
        )

    tab1, tab2, tab3 = st.tabs(
        ["🎯 Hiệu quả khuyến mãi", "↩️ Hành vi trả hàng", "📦 Tồn kho & hết hàng"]
    )

    with tab1:
        if promo_filtered.empty:
            st.info("Không có dữ liệu khuyến mãi theo bộ lọc đã chọn.")
        else:
            with st.container(border=True):
                st.subheader("Promo Performance")
                promo_current, promo_previous = split_current_previous(promo_filtered, "order_date")
                curr_net = promo_current["net_revenue"].sum()
                prev_net = promo_previous["net_revenue"].sum()
                curr_gp = promo_current["gross_profit"].sum()
                prev_gp = promo_previous["gross_profit"].sum()
                curr_margin = curr_gp / curr_net if curr_net > 0 else np.nan
                prev_margin = prev_gp / prev_net if prev_net > 0 else np.nan

                k1, k2, k3 = st.columns(3)
                k1.metric("Net revenue", vnd_format(curr_net), format_rel_delta(curr_net, prev_net))
                k2.metric("Gross profit", vnd_format(curr_gp), format_rel_delta(curr_gp, prev_gp))
                k3.metric("Gross margin", pct_format(curr_margin), format_pp_delta(curr_margin, prev_margin))

            monthly = (
                promo_filtered.groupby(["order_month", "promo_status"], as_index=False)
                .agg(net_revenue=("net_revenue", "sum"))
            )
            fig_monthly = px.line(
                monthly,
                x="order_month",
                y="net_revenue",
                color="promo_status",
                color_discrete_map=PROMO_COLOR_MAP,
                markers=True,
                title="Xu hướng doanh thu thuần theo trạng thái khuyến mãi",
                labels={"order_month": "Tháng", "net_revenue": "Net revenue (VND)"},
            )
            fig_monthly.update_yaxes(tickformat=",.0f")
            plot_chart(fig_monthly)

            margin_by_status = (
                promo_filtered.groupby("promo_status", as_index=False)
                .agg(
                    gross_margin_pct=("gross_margin_pct", "mean"),
                    gross_profit=("gross_profit", "sum"),
                )
                .sort_values("gross_margin_pct", ascending=False)
            )
            fig_margin = px.bar(
                margin_by_status,
                x="promo_status",
                y="gross_margin_pct",
                color="promo_status",
                color_discrete_map=PROMO_COLOR_MAP,
                text=margin_by_status["gross_margin_pct"].map(lambda v: f"{v:.1%}"),
                title="Biên lợi nhuận gộp trung bình theo trạng thái khuyến mãi",
                labels={"promo_status": "Promo status", "gross_margin_pct": "Gross margin"},
            )
            fig_margin.update_yaxes(tickformat=".0%")
            plot_chart(fig_margin)

            top_promos = (
                promo_filtered[promo_filtered["promo_name"].notna()]
                .groupby("promo_name", as_index=False)
                .agg(gross_profit=("gross_profit", "sum"), net_revenue=("net_revenue", "sum"))
                .sort_values("gross_profit", ascending=False)
                .head(top_n)
            )
            if not top_promos.empty:
                fig_top_promos = px.bar(
                    top_promos.sort_values("gross_profit"),
                    x="gross_profit",
                    y="promo_name",
                    orientation="h",
                    title=f"Top {top_n} chiến dịch theo gross profit",
                    labels={"gross_profit": "Gross profit (VND)", "promo_name": "Chiến dịch"},
                )
                fig_top_promos.update_xaxes(tickformat=",.0f")
                plot_chart(fig_top_promos)
                st.dataframe(
                    top_promos.rename(
                        columns={
                            "promo_name": "Campaign",
                            "gross_profit": "Gross profit",
                            "net_revenue": "Net revenue",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "⬇️ Tải CSV - Top campaigns",
                    data=csv_bytes(top_promos),
                    file_name="promo_top_campaigns.csv",
                    mime="text/csv",
                    key="dl_promo_top_campaigns",
                )

            with st.container(border=True):
                st.markdown("### Nhận xét chính")
                best_status = margin_by_status.iloc[0]
                worst_status = margin_by_status.iloc[-1]
                top_promo_name = top_promos.iloc[0]["promo_name"] if not top_promos.empty else "N/A"
                st.markdown(
                    f"- Trạng thái **{best_status['promo_status']}** có biên lợi nhuận cao nhất "
                    f"({best_status['gross_margin_pct']:.2%}).\n"
                    f"- Trạng thái **{worst_status['promo_status']}** thấp nhất "
                    f"({worst_status['gross_margin_pct']:.2%}).\n"
                    f"- Campaign nổi bật nhất theo lợi nhuận: **{top_promo_name}**."
                )
                st.markdown("### Tác động kinh doanh")
                st.markdown(
                    "- Chênh lệch biên lợi nhuận theo trạng thái khuyến mãi cho thấy hiệu quả "
                    "phân bổ ngân sách promotion chưa đồng đều."
                )
                st.markdown("### Khuyến nghị hành động")
                if (
                    "Stacked" in margin_by_status["promo_status"].values
                    and "Single" in margin_by_status["promo_status"].values
                ):
                    stacked_margin = float(
                        margin_by_status.loc[
                            margin_by_status["promo_status"] == "Stacked", "gross_margin_pct"
                        ].iloc[0]
                    )
                    single_margin = float(
                        margin_by_status.loc[
                            margin_by_status["promo_status"] == "Single", "gross_margin_pct"
                        ].iloc[0]
                    )
                    if stacked_margin < single_margin:
                        st.markdown(
                            "- Hạn chế combo mã **Stacked** ở nhóm biên mỏng; ưu tiên **Single** "
                            "cho mục tiêu bảo toàn margin."
                        )
                    else:
                        st.markdown(
                            "- Mở rộng có kiểm soát chiến dịch **Stacked** ở nhóm sản phẩm có biên cao."
                        )
                st.markdown(
                    "- Duy trì ngân sách cho campaign top lợi nhuận, giảm dần campaign có doanh thu "
                    "cao nhưng đóng góp lợi nhuận thấp."
                )

    with tab2:
        if returns_filtered.empty:
            st.info("Không có dữ liệu trả hàng theo bộ lọc đã chọn.")
        else:
            with st.container(border=True):
                st.subheader("Customer Returns")
                returns_current, returns_previous = split_current_previous(returns_filtered, "order_date")
                curr_returns = len(returns_current)
                prev_returns = len(returns_previous)
                curr_refund = returns_current["refund_amount"].sum()
                prev_refund = returns_previous["refund_amount"].sum()
                curr_days = returns_current["days_to_return"].median()
                prev_days = returns_previous["days_to_return"].median()
                days_delta = None
                if np.isfinite(curr_days) and np.isfinite(prev_days):
                    days_delta = f"{curr_days - prev_days:+.1f} ngày"

                r1, r2, r3 = st.columns(3)
                r1.metric("Số lượt trả hàng", f"{curr_returns:,}", format_rel_delta(curr_returns, prev_returns))
                r2.metric("Tổng hoàn tiền", vnd_format(curr_refund), format_rel_delta(curr_refund, prev_refund))
                r3.metric(
                    "Days to return (median)",
                    f"{curr_days:.0f} ngày" if np.isfinite(curr_days) else "N/A",
                    days_delta,
                )

            reason_dist = (
                returns_filtered.groupby("return_reason", as_index=False)
                .agg(returns=("return_id", "count"))
                .sort_values("returns", ascending=False)
            )
            fig_reason = px.bar(
                reason_dist,
                x="return_reason",
                y="returns",
                color="return_reason",
                title="Phân bổ lý do trả hàng",
                labels={"return_reason": "Lý do", "returns": "Số lượt"},
            )
            plot_chart(fig_reason)

            refund_by_category = (
                returns_filtered.groupby("category", as_index=False)
                .agg(refund_amount=("refund_amount", "sum"))
                .sort_values("refund_amount", ascending=False)
                .head(top_n)
            )
            fig_refund = px.bar(
                refund_by_category.sort_values("refund_amount"),
                x="refund_amount",
                y="category",
                orientation="h",
                title=f"Top {top_n} danh mục gây hoàn tiền cao nhất",
                labels={"refund_amount": "Tổng hoàn tiền (VND)", "category": "Danh mục"},
            )
            fig_refund.update_xaxes(tickformat=",.0f")
            plot_chart(fig_refund)

            fig_days = px.box(
                returns_filtered,
                x="return_reason",
                y="days_to_return",
                color="return_reason",
                title="Thời gian trả hàng theo lý do",
                labels={"days_to_return": "Số ngày", "return_reason": "Lý do trả"},
            )
            plot_chart(fig_days)

            st.dataframe(
                reason_dist.rename(
                    columns={
                        "return_reason": "Return reason",
                        "returns": "Return count",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "⬇️ Tải CSV - Return reason breakdown",
                data=csv_bytes(reason_dist),
                file_name="returns_reason_breakdown.csv",
                mime="text/csv",
                key="dl_returns_reason",
            )

            with st.container(border=True):
                st.markdown("### Nhận xét chính")
                top_reason_row = reason_dist.iloc[0]
                top_reason_share = top_reason_row["returns"] / reason_dist["returns"].sum()
                top_refund_category = refund_by_category.iloc[0]["category"]
                st.markdown(
                    f"- Lý do trả hàng chính là **{top_reason_row['return_reason']}**, chiếm "
                    f"**{top_reason_share:.2%}** tổng lượt trả.\n"
                    f"- Danh mục gây hoàn tiền cao nhất: **{top_refund_category}**.\n"
                    f"- Thời gian trả hàng trung vị: **{returns_filtered['days_to_return'].median():.0f} ngày**."
                )
                st.markdown("### Tác động kinh doanh")
                st.markdown(
                    "- Return pattern đang ảnh hưởng trực tiếp đến chi phí hoàn tiền và trải nghiệm "
                    "hậu mua của khách hàng."
                )
                st.markdown("### Khuyến nghị hành động")
                if top_reason_row["return_reason"] == "wrong_size":
                    st.markdown(
                        "- Bổ sung size chart chi tiết theo danh mục và gợi ý size dựa trên lịch sử mua."
                    )
                elif top_reason_row["return_reason"] == "defective":
                    st.markdown(
                        "- Tăng kiểm tra chất lượng trước xuất kho cho nhóm sản phẩm có tỷ lệ lỗi cao."
                    )
                elif top_reason_row["return_reason"] == "late_delivery":
                    st.markdown(
                        "- Rà soát SLA giao hàng theo khu vực để giảm trả hàng do giao trễ."
                    )
                else:
                    st.markdown(
                        "- Thiết kế playbook chăm sóc sau mua cho lý do trả hàng có tần suất cao nhất."
                    )
                st.markdown(
                    "- Theo dõi riêng top danh mục hoàn tiền cao để tối ưu chính sách đổi trả và tồn kho."
                )

    with tab3:
        if inventory_filtered.empty:
            st.info("Không có dữ liệu tồn kho theo bộ lọc đã chọn.")
        else:
            with st.container(border=True):
                st.subheader("Inventory & Stockouts")
                inv_current, inv_previous = split_current_previous(inventory_filtered, "snapshot_date")
                curr_lost = inv_current["est_lost_revenue"].sum()
                prev_lost = inv_previous["est_lost_revenue"].sum()
                curr_overstock = inv_current["overstock_capital_value"].sum()
                prev_overstock = inv_previous["overstock_capital_value"].sum()
                curr_stockout = inv_current["stockout_flag"].mean()
                prev_stockout = inv_previous["stockout_flag"].mean()

                i1, i2, i3 = st.columns(3)
                i1.metric("Ước tính doanh thu mất", vnd_format(curr_lost), format_rel_delta(curr_lost, prev_lost))
                i2.metric("Vốn ứ đọng", vnd_format(curr_overstock), format_rel_delta(curr_overstock, prev_overstock))
                i3.metric("Tỷ lệ tháng stockout", pct_format(curr_stockout), format_pp_delta(curr_stockout, prev_stockout))

            inv_monthly = (
                inventory_filtered.groupby("inventory_month", as_index=False)
                .agg(
                    est_lost_revenue=("est_lost_revenue", "sum"),
                    overstock_capital_value=("overstock_capital_value", "sum"),
                )
            )
            inv_long = inv_monthly.melt(
                id_vars=["inventory_month"],
                value_vars=["est_lost_revenue", "overstock_capital_value"],
                var_name="metric",
                value_name="value",
            )
            fig_inv_monthly = px.line(
                inv_long,
                x="inventory_month",
                y="value",
                color="metric",
                markers=True,
                title="Xu hướng thiệt hại do stockout và overstock theo tháng",
                labels={"inventory_month": "Tháng", "value": "Giá trị (VND)", "metric": "Chỉ số"},
            )
            fig_inv_monthly.update_yaxes(tickformat=",.0f")
            plot_chart(fig_inv_monthly)

            lost_by_category = (
                inventory_filtered.groupby("category", as_index=False)
                .agg(est_lost_revenue=("est_lost_revenue", "sum"))
                .sort_values("est_lost_revenue", ascending=False)
                .head(top_n)
            )
            fig_lost_cat = px.bar(
                lost_by_category.sort_values("est_lost_revenue"),
                x="est_lost_revenue",
                y="category",
                orientation="h",
                title=f"Top {top_n} danh mục thất thoát doanh thu do hết hàng",
                labels={"est_lost_revenue": "Estimated lost revenue (VND)", "category": "Danh mục"},
            )
            fig_lost_cat.update_xaxes(tickformat=",.0f")
            plot_chart(fig_lost_cat)

            scatter_sample = inventory_filtered.copy()
            scatter_sample["stockout_flag"] = scatter_sample["stockout_flag"].astype(str)
            fig_scatter = px.scatter(
                scatter_sample,
                x="stock_on_hand",
                y="sell_through_rate",
                size="est_lost_revenue",
                color="stockout_flag",
                hover_data=["product_name", "category", "segment", "stockout_days"],
                title="Stock on hand vs sell-through-rate (kích thước = lost revenue)",
                labels={
                    "stock_on_hand": "Tồn kho cuối kỳ",
                    "sell_through_rate": "Sell-through rate",
                    "stockout_flag": "Stockout flag",
                },
            )
            fig_scatter.update_traces(marker=dict(opacity=0.68, line=dict(width=0.25, color="#FFFFFF")))
            fig_scatter.update_layout(
                plot_bgcolor="#0F1117",
                paper_bgcolor="#0F1117",
                font=dict(color="#E5E7EB"),
                title_font=dict(color="#F9FAFB", size=30),
                legend=dict(
                    bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E5E7EB"),
                    title_font=dict(color="#E5E7EB"),
                ),
                hoverlabel=dict(bgcolor="#111827", font_color="#F9FAFB"),
            )
            fig_scatter.update_xaxes(
                gridcolor="#374151",
                zerolinecolor="#374151",
                title_font=dict(color="#E5E7EB"),
                tickfont=dict(color="#CBD5E1"),
            )
            fig_scatter.update_yaxes(
                gridcolor="#374151",
                zerolinecolor="#374151",
                title_font=dict(color="#E5E7EB"),
                tickfont=dict(color="#CBD5E1"),
            )
            fig_scatter.update_yaxes(tickformat=".0%")
            plot_chart(fig_scatter)

            st.dataframe(
                lost_by_category.rename(
                    columns={
                        "category": "Category",
                        "est_lost_revenue": "Estimated lost revenue",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "⬇️ Tải CSV - Lost revenue by category",
                data=csv_bytes(lost_by_category),
                file_name="inventory_lost_revenue_by_category.csv",
                mime="text/csv",
                key="dl_inventory_lost_revenue",
            )

            with st.container(border=True):
                st.markdown("### Nhận xét chính")
                top_lost_category = lost_by_category.iloc[0]["category"]
                total_lost_revenue = inventory_filtered["est_lost_revenue"].sum()
                total_overstock = inventory_filtered["overstock_capital_value"].sum()
                st.markdown(
                    f"- Danh mục thất thoát doanh thu do hết hàng cao nhất: **{top_lost_category}**.\n"
                    f"- Tổng thất thoát ước tính do stockout: **{vnd_format(total_lost_revenue)}**.\n"
                    f"- Vốn ứ đọng do overstock: **{vnd_format(total_overstock)}**."
                )
                st.markdown("### Tác động kinh doanh")
                st.markdown(
                    "- Mất cân đối giữa stockout và overstock làm giảm doanh thu tiềm năng và tăng chi phí vốn."
                )
                st.markdown("### Khuyến nghị hành động")
                if total_lost_revenue > total_overstock:
                    st.markdown(
                        "- Ưu tiên giảm **stockout**: tăng reorder point cho nhóm sản phẩm bán nhanh."
                    )
                else:
                    st.markdown(
                        "- Ưu tiên giải phóng **overstock**: triển khai chương trình đẩy bán có kiểm soát."
                    )
                st.markdown(
                    "- Thiết lập cảnh báo sớm theo tháng cho sản phẩm có **stockout_days** cao và "
                    "**sell_through_rate** cao đồng thời."
                )


if __name__ == "__main__":
    main()
