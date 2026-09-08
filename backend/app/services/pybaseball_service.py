from pybaseball import statcast, cache


cache.enable()


def get_statcast_data(start_date: str, end_date: str):
    return statcast(
        start_dt=start_date,
        end_dt=end_date
    )


if __name__ == "__main__":
    data = get_statcast_data(
        "2025-07-01",
        "2025-07-01"
    )

    print(data.head())
    print()
    print("Rows:", len(data))
    print()
    print(data.columns.tolist())
