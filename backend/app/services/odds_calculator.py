from typing import Optional, Union

Number = Union[int, float, str]


class CalculatorError(ValueError):
    """Raised when the calculator receives invalid input."""
    pass


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _is_empty(value: Optional[Number]) -> bool:
    """Return True if a field should be treated as empty."""
    return value is None or (
        isinstance(value, str) and value.strip() == ""
    )


def _to_float(value: Number, field_name: str) -> float:
    """
    Convert user input into a float.

    Supports inputs such as:
        "+150"
        "-200"
        "2.50"
        "40%"
        "$100"
        "1,000"
    """
    try:
        if isinstance(value, str):
            value = (
                value.strip()
                .replace("$", "")
                .replace("%", "")
                .replace(",", "")
            )

        return float(value)

    except (TypeError, ValueError):
        raise CalculatorError(
            f"{field_name} must be a valid number."
        )


# ============================================================
# ODDS CONVERSIONS
# ============================================================

def american_to_decimal(american_odds: Number) -> float:
    """Convert American odds to decimal odds."""

    odds = _to_float(
        american_odds,
        "American odds"
    )

    if -100 < odds < 100:
        raise CalculatorError(
            "American odds must be +100 or greater, "
            "or -100 or lower."
        )

    if odds > 0:
        return 1 + (odds / 100)

    return 1 + (100 / abs(odds))


def decimal_to_american(decimal_odds: Number) -> float:
    """Convert decimal odds to American odds."""

    odds = _to_float(
        decimal_odds,
        "Decimal odds"
    )

    if odds <= 1:
        raise CalculatorError(
            "Decimal odds must be greater than 1.00."
        )

    if odds >= 2:
        return (odds - 1) * 100

    return -100 / (odds - 1)


def decimal_to_percentage(decimal_odds: Number) -> float:
    """Convert decimal odds into implied win probability."""

    odds = _to_float(
        decimal_odds,
        "Decimal odds"
    )

    if odds <= 1:
        raise CalculatorError(
            "Decimal odds must be greater than 1.00."
        )

    return 100 / odds


def percentage_to_decimal(percentage: Number) -> float:
    """Convert implied probability into decimal odds."""

    probability = _to_float(
        percentage,
        "Percentage"
    )

    if probability <= 0 or probability >= 100:
        raise CalculatorError(
            "Percentage must be greater than 0 "
            "and less than 100."
        )

    return 100 / probability


# ============================================================
# MAIN CALCULATOR
# ============================================================

def calculate_bet(
    odds: Optional[Number] = None,
    odds_type: str = "american",
    percentage: Optional[Number] = None,
    money_input: Optional[Number] = None,
    profit: Optional[Number] = None,
    money_output: Optional[Number] = None,
) -> dict:
    """
    Calculate missing betting values.

    VALID INPUT COMBINATIONS:

    1. Odds only
       -> calculates percentage

    2. Percentage only
       -> calculates odds

    3. Odds + ONE money field
       -> calculates percentage and remaining money fields

    4. Percentage + ONE money field
       -> calculates odds and remaining money fields

    5. TWO money fields with no odds/percentage
       -> calculates missing money field, odds, and percentage


    INVALID INPUT COMBINATIONS:

    - Nothing entered
    - Only ONE money field
    - Odds AND percentage entered
    - Odds/percentage + TWO money fields
    - All THREE money fields
    """

    # ========================================================
    # VALIDATE ODDS TYPE
    # ========================================================

    odds_type = odds_type.strip().lower()

    if odds_type not in {"american", "decimal"}:
        raise CalculatorError(
            "Odds type must be 'american' or 'decimal'."
        )

    # ========================================================
    # DETERMINE ENTERED FIELDS
    # ========================================================

    odds_entered = not _is_empty(odds)
    percentage_entered = not _is_empty(percentage)

    money_values = {
        "money_input": money_input,
        "profit": profit,
        "money_output": money_output,
    }

    entered_money_fields = [
        name
        for name, value in money_values.items()
        if not _is_empty(value)
    ]

    money_count = len(entered_money_fields)

    # ========================================================
    # VALIDATE INPUT COMBINATIONS
    # ========================================================

    # Cannot manually enter both odds and percentage.
    if odds_entered and percentage_entered:
        raise CalculatorError(
            "Enter either odds or percentage, not both."
        )

    # Cannot manually enter all three money fields.
    if money_count == 3:
        raise CalculatorError(
            "Enter at most two money values."
        )

    # If odds OR percentage is entered,
    # only one money field can also be entered.
    if (
        (odds_entered or percentage_entered)
        and money_count > 1
    ):
        raise CalculatorError(
            "When odds or percentage is entered, "
            "enter at most one money value."
        )

    # No odds/percentage and no money values.
    if (
        not odds_entered
        and not percentage_entered
        and money_count == 0
    ):
        raise CalculatorError(
            "Enter odds, percentage, or two money values."
        )

    # No odds/percentage and only ONE money value.
    # There is not enough information to calculate anything.
    if (
        not odds_entered
        and not percentage_entered
        and money_count == 1
    ):
        raise CalculatorError(
            "A single money value is not enough. "
            "Enter odds or percentage, or enter a second money value."
        )

    # ========================================================
    # PARSE MONEY VALUES
    # ========================================================

    stake = (
        _to_float(
            money_input,
            "Money input"
        )
        if not _is_empty(money_input)
        else None
    )

    final_profit = (
        _to_float(
            profit,
            "Profit"
        )
        if not _is_empty(profit)
        else None
    )

    final_output = (
        _to_float(
            money_output,
            "Money output"
        )
        if not _is_empty(money_output)
        else None
    )

    # All entered money values must be positive.
    money_fields = {
        "Money input": stake,
        "Profit": final_profit,
        "Money output": final_output,
    }

    for name, value in money_fields.items():
        if value is not None and value <= 0:
            raise CalculatorError(
                f"{name} must be greater than 0."
            )

    # ========================================================
    # DETERMINE DECIMAL ODDS
    # ========================================================

    decimal_odds = None

    # --------------------------------------------------------
    # CASE 1:
    # User entered odds.
    # --------------------------------------------------------

    if odds_entered:

        if odds_type == "american":
            decimal_odds = american_to_decimal(
                odds
            )

        else:
            decimal_odds = _to_float(
                odds,
                "Decimal odds"
            )

            if decimal_odds <= 1:
                raise CalculatorError(
                    "Decimal odds must be greater than 1.00."
                )

    # --------------------------------------------------------
    # CASE 2:
    # User entered percentage.
    # --------------------------------------------------------

    elif percentage_entered:

        decimal_odds = percentage_to_decimal(
            percentage
        )

    # --------------------------------------------------------
    # CASE 3:
    # No odds or percentage.
    # TWO money fields must have been supplied.
    # Use those two values to determine the odds.
    # --------------------------------------------------------

    elif money_count == 2:

        # ====================================================
        # Money Input + Profit
        # ====================================================

        if (
            stake is not None
            and final_profit is not None
        ):

            final_output = stake + final_profit

            decimal_odds = (
                final_output / stake
            )

        # ====================================================
        # Money Input + Money Output
        # ====================================================

        elif (
            stake is not None
            and final_output is not None
        ):

            if final_output <= stake:
                raise CalculatorError(
                    "Money output must be greater "
                    "than money input."
                )

            final_profit = (
                final_output - stake
            )

            decimal_odds = (
                final_output / stake
            )

        # ====================================================
        # Profit + Money Output
        # ====================================================

        elif (
            final_profit is not None
            and final_output is not None
        ):

            if final_output <= final_profit:
                raise CalculatorError(
                    "Money output must be greater "
                    "than profit."
                )

            stake = (
                final_output - final_profit
            )

            decimal_odds = (
                final_output / stake
            )

    # ========================================================
    # CALCULATE ODDS + PERCENTAGE
    # ========================================================

    american_odds = decimal_to_american(
        decimal_odds
    )

    implied_percentage = decimal_to_percentage(
        decimal_odds
    )

    # ========================================================
    # CALCULATE MONEY VALUES
    #
    # Only needed when odds/percentage + ONE money value
    # was originally entered.
    # ========================================================

    if money_count == 1:

        # ----------------------------------------------------
        # Money Input supplied
        # ----------------------------------------------------

        if stake is not None:

            final_profit = (
                stake * (decimal_odds - 1)
            )

            final_output = (
                stake * decimal_odds
            )

        # ----------------------------------------------------
        # Desired Profit supplied
        # ----------------------------------------------------

        elif final_profit is not None:

            stake = (
                final_profit
                / (decimal_odds - 1)
            )

            final_output = (
                stake + final_profit
            )

        # ----------------------------------------------------
        # Desired Money Output supplied
        # ----------------------------------------------------

        elif final_output is not None:

            stake = (
                final_output
                / decimal_odds
            )

            final_profit = (
                final_output - stake
            )

    # ========================================================
    # DETERMINE DISPLAYED ODDS FORMAT
    # ========================================================

    if odds_type == "american":
        displayed_odds = american_odds

    else:
        displayed_odds = decimal_odds

    # ========================================================
    # RETURN ALL FIVE CALCULATOR VALUES
    # ========================================================

    return {
        "odds": round(displayed_odds, 2),
        "odds_type": odds_type,

        # Useful for switching formats on the frontend later.
        "american_odds": round(american_odds, 2),
        "decimal_odds": round(decimal_odds, 4),

        "percentage": round(
            implied_percentage,
            2
        ),

        "money_input": (
            round(stake, 2)
            if stake is not None
            else None
        ),

        "profit": (
            round(final_profit, 2)
            if final_profit is not None
            else None
        ),

        "money_output": (
            round(final_output, 2)
            if final_output is not None
            else None
        ),
    }
