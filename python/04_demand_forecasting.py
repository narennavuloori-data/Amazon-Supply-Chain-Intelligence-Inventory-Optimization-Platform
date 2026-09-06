from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

SALES_FILE = PROCESSED_DIR / "sales_features.csv"
PRODUCTS_FILE = PROCESSED_DIR / "products_features.csv"

FORECAST_FILE = PROCESSED_DIR / "demand_forecast_results.csv"
PERFORMANCE_FILE = PROCESSED_DIR / "demand_model_performance.csv"

TOP_COMBINATIONS = 50
TEST_WEEKS = 8
FORECAST_WEEKS = 8
MOVING_AVERAGE_WEEKS = 4
ALPHA = 0.30
RANDOM_SEED = 42


def check_files():
    missing = []

    if not SALES_FILE.exists():
        missing.append(str(SALES_FILE))

    if not PRODUCTS_FILE.exists():
        missing.append(str(PRODUCTS_FILE))

    if missing:
        raise FileNotFoundError(
            "Missing file(s):\n" + "\n".join(missing)
        )


def load_data():
    # loading sales and product data
    sales = pd.read_csv(
        SALES_FILE,
        usecols=[
            "order_date",
            "warehouse_id",
            "product_id",
            "net_units_sold",
        ],
        parse_dates=["order_date"],
    )

    products = pd.read_csv(
        PRODUCTS_FILE,
        usecols=["product_id", "product_name"],
    )

    sales["net_units_sold"] = pd.to_numeric(
        sales["net_units_sold"],
        errors="coerce",
    ).fillna(0)

    return sales, products


def select_top_combinations(sales):
    # selecting important product and warehouse combinations
    top = (
        sales.groupby(
            ["warehouse_id", "product_id"],
            as_index=False,
        )["net_units_sold"]
        .sum()
        .sort_values("net_units_sold", ascending=False)
        .head(TOP_COMBINATIONS)
    )

    return top[["warehouse_id", "product_id"]]


def create_weekly_demand(sales, warehouse_id, product_id, global_end_week):
    data = sales[
        (sales["warehouse_id"] == warehouse_id)
        & (sales["product_id"] == product_id)
    ].copy()

    if data.empty:
        return pd.DataFrame()

    data["week_start"] = (
        data["order_date"].dt.to_period("W").dt.start_time
    )

    weekly = (
        data.groupby("week_start", as_index=False)["net_units_sold"]
        .sum()
        .rename(columns={"net_units_sold": "demand"})
    )

    full_weeks = pd.date_range(
        start=weekly["week_start"].min(),
        end=global_end_week,
        freq="7D",
    )

    weekly = (
        weekly.set_index("week_start")
        .reindex(full_weeks, fill_value=0)
        .rename_axis("week_start")
        .reset_index()
    )

    weekly["demand"] = weekly["demand"].astype(float)

    return weekly


def moving_average_test(train_values, test_values):
    history = list(train_values)
    predictions = []

    # predicting each test week from recent demand
    for actual in test_values:
        recent = history[-MOVING_AVERAGE_WEEKS:]
        prediction = np.mean(recent)

        predictions.append(max(0, prediction))
        history.append(actual)

    return np.array(predictions)


def exponential_smoothing_test(train_values, test_values):
    level = float(train_values[0])

    # calculating the latest smoothed demand level
    for value in train_values[1:]:
        level = ALPHA * value + (1 - ALPHA) * level

    predictions = []

    for actual in test_values:
        predictions.append(max(0, level))
        level = ALPHA * actual + (1 - ALPHA) * level

    return np.array(predictions)


def create_rf_row(history, forecast_date):
    recent = history[-MOVING_AVERAGE_WEEKS:]

    return [
        history[-1],
        history[-2],
        history[-3],
        history[-4],
        np.mean(recent),
        forecast_date.isocalendar().week,
        forecast_date.month,
    ]


def train_random_forest(train_dates, train_values):
    x = []
    y = []

    # creating lag features from past weekly demand
    for i in range(MOVING_AVERAGE_WEEKS, len(train_values)):
        history = list(train_values[:i])

        x.append(
            create_rf_row(
                history,
                train_dates.iloc[i],
            )
        )
        y.append(train_values[i])

    model = RandomForestRegressor(
        n_estimators=50,
        max_depth=6,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    model.fit(x, y)

    return model


def random_forest_test(model, train_values, test_dates, test_values):
    history = list(train_values)
    predictions = []

    # testing one week at a time
    for i, actual in enumerate(test_values):
        row = create_rf_row(history, test_dates.iloc[i])
        prediction = model.predict([row])[0]

        predictions.append(max(0, prediction))
        history.append(actual)

    return np.array(predictions)


def calculate_metrics(actual, predicted):
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))

    valid = actual > 0

    if valid.any():
        mape = np.mean(
            np.abs(
                (actual[valid] - predicted[valid])
                / actual[valid]
            )
        ) * 100
    else:
        mape = np.nan

    accuracy = np.nan

    if not np.isnan(mape):
        accuracy = max(0, 100 - mape)

    return round(mae, 2), round(rmse, 2), round(mape, 2), round(accuracy, 2)


def moving_average_future(history, weeks):
    values = list(history)
    forecasts = []

    # forecasting future demand from the recent average
    for _ in range(weeks):
        prediction = np.mean(
            values[-MOVING_AVERAGE_WEEKS:]
        )

        prediction = max(0, prediction)
        forecasts.append(prediction)
        values.append(prediction)

    return forecasts


def exponential_smoothing_future(history, weeks):
    level = float(history[0])

    for value in history[1:]:
        level = ALPHA * value + (1 - ALPHA) * level

    return [max(0, level)] * weeks


def random_forest_future(model, dates, history):
    values = list(history)
    forecasts = []

    # forecasting future weeks using predicted demand as history
    for forecast_date in dates:
        row = create_rf_row(values, forecast_date)
        prediction = model.predict([row])[0]

        prediction = max(0, prediction)
        forecasts.append(prediction)
        values.append(prediction)

    return forecasts


def evaluate_combination(weekly, warehouse_id, product_id):
    if len(weekly) < TEST_WEEKS + 20:
        return None

    train = weekly.iloc[:-TEST_WEEKS].copy()
    test = weekly.iloc[-TEST_WEEKS:].copy()

    train_values = train["demand"].to_numpy()
    test_values = test["demand"].to_numpy()

    ma_predictions = moving_average_test(
        train_values,
        test_values,
    )

    es_predictions = exponential_smoothing_test(
        train_values,
        test_values,
    )

    rf_model = train_random_forest(
        train["week_start"],
        train_values,
    )

    rf_predictions = random_forest_test(
        rf_model,
        train_values,
        test["week_start"],
        test_values,
    )

    predictions = {
        "Moving Average": ma_predictions,
        "Exponential Smoothing": es_predictions,
        "Random Forest": rf_predictions,
    }

    performance = []

    for model_name, predicted in predictions.items():
        mae, rmse, mape, accuracy = calculate_metrics(
            test_values,
            predicted,
        )

        performance.append(
            {
                "warehouse_id": warehouse_id,
                "product_id": product_id,
                "model": model_name,
                "mae": mae,
                "rmse": rmse,
                "mape": mape,
                "forecast_accuracy": accuracy,
            }
        )

    performance_df = pd.DataFrame(performance)

    best_model = performance_df.sort_values(
        "mae"
    ).iloc[0]["model"]

    return performance_df, best_model, rf_model


def create_future_forecast(
    weekly,
    warehouse_id,
    product_id,
    product_name,
    best_model,
    rf_model,
    accuracy,
):
    last_week = weekly["week_start"].max()

    future_dates = pd.date_range(
        start=last_week + pd.Timedelta(days=7),
        periods=FORECAST_WEEKS,
        freq="7D",
    )

    history = weekly["demand"].to_numpy()

    if best_model == "Moving Average":
        forecasts = moving_average_future(
            history,
            FORECAST_WEEKS,
        )

    elif best_model == "Exponential Smoothing":
        forecasts = exponential_smoothing_future(
            history,
            FORECAST_WEEKS,
        )

    else:
        forecasts = random_forest_future(
            rf_model,
            future_dates,
            history,
        )

    rows = []

    for date, forecast in zip(future_dates, forecasts):
        rows.append(
            {
                "forecast_week": date.date(),
                "warehouse_id": warehouse_id,
                "product_id": product_id,
                "product_name": product_name,
                "forecast_units": round(forecast, 2),
                "selected_model": best_model,
                "model_accuracy": accuracy,
            }
        )

    return rows


def main():
    check_files()

    sales, products = load_data()
    top_combinations = select_top_combinations(sales)

    product_names = products.set_index(
        "product_id"
    )["product_name"].to_dict()

    global_end_week = (
        sales["order_date"].max().to_period("W").start_time
    )

    all_performance = []
    all_forecasts = []

    print("DEMAND FORECASTING")
    print("-" * 55)

    for _, row in top_combinations.iterrows():
        warehouse_id = row["warehouse_id"]
        product_id = row["product_id"]

        weekly = create_weekly_demand(
            sales,
            warehouse_id,
            product_id,
            global_end_week,
        )

        result = evaluate_combination(
            weekly,
            warehouse_id,
            product_id,
        )

        if result is None:
            continue

        performance, best_model, rf_model = result

        performance["best_model"] = (
            performance["model"] == best_model
        ).astype("int8")

        all_performance.append(performance)

        best_row = performance[
            performance["model"] == best_model
        ].iloc[0]

        product_name = product_names.get(
            product_id,
            "Unknown Product",
        )

        future_rows = create_future_forecast(
            weekly,
            warehouse_id,
            product_id,
            product_name,
            best_model,
            rf_model,
            best_row["forecast_accuracy"],
        )

        all_forecasts.extend(future_rows)

    if not all_performance:
        raise ValueError(
            "Not enough historical demand was found for forecasting."
        )

    performance_df = pd.concat(
        all_performance,
        ignore_index=True,
    )

    forecast_df = pd.DataFrame(all_forecasts)

    performance_df.to_csv(
        PERFORMANCE_FILE,
        index=False,
    )

    forecast_df.to_csv(
        FORECAST_FILE,
        index=False,
    )

    model_summary = (
        performance_df.groupby("model", as_index=False)
        .agg(
            average_mae=("mae", "mean"),
            average_rmse=("rmse", "mean"),
            average_mape=("mape", "mean"),
            average_accuracy=("forecast_accuracy", "mean"),
        )
        .round(2)
    )

    print(f"Combinations forecasted: {performance_df['product_id'].count() // 3}")
    print(f"Future weeks: {FORECAST_WEEKS}")
    print()
    print(model_summary.to_string(index=False))
    print()
    print(f"Performance saved to: {PERFORMANCE_FILE}")
    print(f"Forecast saved to: {FORECAST_FILE}")


if __name__ == "__main__":
    main()
