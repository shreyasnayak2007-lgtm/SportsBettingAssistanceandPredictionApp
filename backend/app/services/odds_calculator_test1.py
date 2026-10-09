from odds_calculator import calculate_bet, CalculatorError


def run_test(description, **kwargs):
    print(f"\n--- {description} ---")

    try:
        result = calculate_bet(**kwargs)

        for key, value in result.items():
            print(f"{key}: {value}")

    except CalculatorError as error:
        print(f"ERROR: {error}")


run_test(
    "American odds + money input",
    odds=150,
    odds_type="american",
    money_input=100
)

run_test(
    "Negative American odds only",
    odds=-200,
    odds_type="american"
)

run_test(
    "Percentage + profit",
    percentage=75,
    profit=100
)

run_test(
    "Two money values",
    money_input=100,
    profit=150
)

run_test(
    "Decimal odds + money output",
    odds=2.5,
    odds_type="decimal",
    money_output=250
)

run_test(
    "Invalid: only one money value",
    money_input=100
)

run_test(
    "Invalid: odds and percentage",
    odds=150,
    percentage=40
)
