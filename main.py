"""
College Budget Buddy
A Drafter website that helps college students plan a monthly budget,
see where their money goes, and figure out how long a savings goal will take.
"""
# ADVANCED TECHNIQUE (not covered in class): try/except.
# matplotlib is an extra library used to draw the budget diagram. It must be imported
# BEFORE drafter (drafter replaces Python's open() function, which matplotlib needs
# while loading). "Agg" tells matplotlib to draw pictures without opening a window.
# If matplotlib is missing, the site still works and shows a text diagram instead.
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    CHARTS_AVAILABLE = True
except Exception:
    CHARTS_AVAILABLE = False

from drafter import *
from dataclasses import dataclass
import math

# ADVANCED TECHNIQUE: these two calls make the site look like a normal website by
# hiding Drafter's debug panel and frame. They are wrapped in try/except so that an
# older Drafter version without these functions doesn't crash the program.
try:
    hide_debug_information()
    set_website_framed(False)
except NameError:
    pass

# Global CONSTANTS are allowed (they never change).
BAR_WIDTH = 12          # how many characters wide the text bars are
SAVINGS_RATE = 0.50     # we recommend saving half of the money left after expenses
CATEGORY_CHOICES = ["Rent/Housing", "Groceries", "Eating Out", "Transportation",
                    "Entertainment", "Subscriptions", "School Supplies", "Other"]
SLICE_COLORS = {"Needs": "#2E86AB", "Wants": "#F18F01",
                "Savings": "#4C9F70", "Free to spend": "#9B8EC4"}


# =====================================
# DATACLASSES
# =====================================

@dataclass
class Expense:
    """One monthly expense the student entered."""
    category: str
    monthly_cost: float
    is_essential: bool   # True = a need (rent, groceries), False = a want (fun stuff)
    note: str


@dataclass
class State:
    """Everything the website remembers about the student."""
    student_name: str
    monthly_income: float
    current_savings: float
    savings_goal: float
    expenses: list[Expense]


# =====================================
# HELPER FUNCTIONS (no Drafter pages in here, so they are easy to test)
# =====================================

def money(amount: float) -> str:
    """Format a number as dollars, like 1234.5 -> '$1,234.50'."""
    # format(x, ",.2f") puts commas in and keeps exactly 2 decimals.
    # (It was not covered in class: it is Python's built-in number formatting.)
    if amount < 0:
        return "-$" + format(-amount, ",.2f")
    return "$" + format(amount, ",.2f")


def total_expenses(expenses: list[Expense]) -> float:
    """Add up the monthly cost of every expense."""
    total = 0.0
    for expense in expenses:
        total = total + expense.monthly_cost
    return total


def total_by_type(expenses: list[Expense], essential: bool) -> float:
    """Add up only the needs (essential=True) or only the wants (essential=False)."""
    total = 0.0
    for expense in expenses:
        if expense.is_essential == essential:
            total = total + expense.monthly_cost
    return total


def monthly_savings(income: float, expense_total: float) -> float:
    """Recommend saving a share of whatever is left after expenses (never below 0)."""
    leftover = income - expense_total
    if leftover <= 0:
        return 0.0
    return leftover * SAVINGS_RATE


def months_to_goal(current: float, goal: float, saved_per_month: float) -> int:
    """Months until the goal is reached. 0 = already there, -1 = can't save yet."""
    amount_left = goal - current
    if amount_left <= 0:
        return 0
    if saved_per_month <= 0:
        return -1
    return math.ceil(amount_left / saved_per_month)


def budget_grade(income: float, expense_total: float) -> str:
    """Give a fun grade based on what share of income goes to expenses."""
    if income <= 0:
        return "❓ Add your income to get a grade!"
    ratio = expense_total / income
    if ratio > 1:
        return "🚨 Over budget"
    if ratio > 0.8:
        return "😬 Tight budget"
    if ratio > 0.5:
        return "😎 Solid budget"
    return "🤑 Superstar saver"


def make_bar(amount: float, maximum: float, width: int) -> str:
    """Draw a text bar, like make_bar(5, 10, 10) -> '█████░░░░░'."""
    if maximum <= 0 or amount <= 0:
        filled = 0
    else:
        filled = round(amount / maximum * width)
    return "█" * filled + "░" * (width - filled)


def unique_categories(expenses: list[Expense]) -> list[str]:
    """List each expense category once, in the order they were added."""
    categories = []
    for expense in expenses:
        if expense.category not in categories:
            categories.append(expense.category)
    return categories


def find_expense_index(expenses: list[Expense], category: str) -> int:
    """Return the position of the first expense in this category, or -1 if none."""
    for position in range(len(expenses)):
        if expenses[position].category == category:
            return position
    return -1


def biggest_want(expenses: list[Expense]) -> str:
    """Return the category of the most expensive 'want', or '' if there are none."""
    best_category = ""
    best_cost = 0.0
    for expense in expenses:
        if not expense.is_essential and expense.monthly_cost > best_cost:
            best_category = expense.category
            best_cost = expense.monthly_cost
    return best_category


def expense_chart_lines(expenses: list[Expense]) -> list[str]:
    """Make one text-chart line per expense, with bars scaled to the biggest expense."""
    biggest = 0.0
    for expense in expenses:
        if expense.monthly_cost > biggest:
            biggest = expense.monthly_cost

    lines = []
    for expense in expenses:
        icon = "🏠" if expense.is_essential else "🎉"
        line = (make_bar(expense.monthly_cost, biggest, BAR_WIDTH) + "  " + icon + " " +
                expense.category + ": " + money(expense.monthly_cost))
        if expense.note != "":
            line = line + "  (" + expense.note + ")"
        lines.append(line)
    return lines


def goal_message(months: int) -> str:
    """Turn the months-to-goal number into a friendly message."""
    if months == 0:
        return "🎉 You've already hit your savings goal!"
    if months > 0:
        return "⏳ About " + str(months) + " month(s) until you reach your goal."
    return "🛑 No money is left to save yet. Try trimming a want or two."


# ---------- helpers for the final budget diagram ----------

def get_cost(expense: Expense) -> float:
    """Return an expense's cost (used as the sorting key below)."""
    return expense.monthly_cost


def sort_expenses_by_cost(expenses: list[Expense]) -> list[Expense]:
    """Return a new list of the expenses, most expensive first."""
    # ADVANCED TECHNIQUE: sorted() with key= and reverse=True.
    # key= tells sorted() which value to compare; reverse=True puts the biggest first.
    return sorted(expenses, key=get_cost, reverse=True)


def budget_slices(income: float, expenses: list[Expense]) -> list[tuple]:
    """Split income into (label, amount) slices: Needs, Wants, Savings, Free to spend.
    Slices that are zero or negative (like 'free' when over budget) are left out."""
    needs = total_by_type(expenses, True)
    wants = total_by_type(expenses, False)
    saved = monthly_savings(income, needs + wants)
    free = income - needs - wants - saved

    slices = []
    for label, amount in [("Needs", needs), ("Wants", wants),
                          ("Savings", saved), ("Free to spend", free)]:
        if amount > 0:
            slices.append((label, amount))
    return slices


def slice_text_lines(slices: list[tuple]) -> list[str]:
    """Text version of the diagram (used if matplotlib isn't installed)."""
    total = 0.0
    for label, amount in slices:
        total = total + amount

    lines = []
    for label, amount in slices:
        percent = round(amount / total * 100)
        lines.append(make_bar(amount, total, BAR_WIDTH) + "  " + label + ": " +
                     money(amount) + " (" + str(percent) + "%)")
    return lines


def draw_budget_diagram(state: State, slices: list[tuple]) -> None:
    """Draw the two-part budget diagram with matplotlib (donut + expense bars).
    NOTE: this function draws a picture, so it can't be unit tested with assert_equal;
    the numbers behind it (budget_slices, sort_expenses_by_cost) are tested instead."""
    figure, (donut, bars) = plt.subplots(1, 2, figsize=(11, 4.8),
                                         gridspec_kw={"width_ratios": [1, 1.2]})

    # Left: donut chart of how the income is split up.
    labels = [label for label, amount in slices]
    amounts = [amount for label, amount in slices]
    colors = [SLICE_COLORS[label] for label in labels]
    donut.pie(amounts, labels=labels, colors=colors, autopct="%1.0f%%", startangle=90,
              pctdistance=0.78, wedgeprops={"width": 0.45, "edgecolor": "white"})
    donut.text(0, 0, money(state.monthly_income) + "\nper month", ha="center",
               va="center", fontsize=12, fontweight="bold")
    donut.set_title("Where your income goes", fontweight="bold")

    # Right: one bar per expense, biggest on top, blue = need, orange = want.
    ordered = sort_expenses_by_cost(state.expenses)
    positions = list(range(len(ordered)))
    costs = [expense.monthly_cost for expense in ordered]
    bar_colors = [SLICE_COLORS["Needs"] if expense.is_essential else SLICE_COLORS["Wants"]
                  for expense in ordered]
    drawn = bars.barh(positions, costs, color=bar_colors)
    bars.set_yticks(positions)
    bars.set_yticklabels([expense.category for expense in ordered])
    bars.invert_yaxis()
    bars.bar_label(drawn, labels=[money(cost) for cost in costs], padding=4)
    bars.set_xlim(0, max(costs + [1]) * 1.25)
    bars.set_title("Your expenses", fontweight="bold")
    bars.legend(handles=[Patch(color=SLICE_COLORS["Needs"], label="Need"),
                         Patch(color=SLICE_COLORS["Wants"], label="Want")],
                loc="lower right")
    for side in ["top", "right"]:
        bars.spines[side].set_visible(False)
    figure.tight_layout()


def diagram_content(state: State) -> list:
    """Return the page pieces for the final diagram (picture, or text if no charts)."""
    slices = budget_slices(state.monthly_income, state.expenses)
    if len(slices) == 0 or len(state.expenses) == 0:
        return ["Add your income and some expenses to see your diagram!"]
    if not CHARTS_AVAILABLE:
        return slice_text_lines(slices)
    draw_budget_diagram(state, slices)
    return [MatPlotLibPlot()]


# =====================================
# ROUTE 1: HOME
# =====================================

@route
def index(state: State) -> Page:
    """Home page with a welcome message and start buttons."""
    greeting = "Welcome!"
    if state.student_name != "":
        greeting = "Welcome back, " + state.student_name + "!"
    return Page(state, [
        Header("💰 College Budget Buddy"),
        Header("Spend smart. Stress less. 🍕", 2),
        greeting,
        "Tell us what you earn and spend each month, and we'll show you where your money goes, "
        "how much you can save, and how long your savings goal will take.",
        "",
        Button("Let's Go! 🚀", "setup_page"),
        Button("Jump to my dashboard 📊", "dashboard")
    ])


# =====================================
# ROUTE 2 + 3: ABOUT YOU (form page, then the route that saves it)
# =====================================

@route
def setup_page(state: State) -> Page:
    """Form asking for the student's name, income, savings, and goal."""
    return Page(state, [
        Header("👋 About You"),
        "What should we call you?",
        TextBox("student_name", state.student_name),
        "Monthly income ($): job, allowance, financial aid, etc.",
        TextBox("monthly_income", str(state.monthly_income)),
        "Money you've saved so far ($):",
        TextBox("current_savings", str(state.current_savings)),
        "Savings goal ($): a trip, a laptop, an emergency fund...",
        TextBox("savings_goal", str(state.savings_goal)),
        "",
        Button("Next: My Expenses ➡️", "save_setup")
    ])


@route
def save_setup(state: State, student_name: str, monthly_income: float,
               current_savings: float, savings_goal: float) -> Page:
    """Save the student's info, or show an error if any amount is negative."""
    if monthly_income < 0 or current_savings < 0 or savings_goal < 0:
        return Page(state, [
            Header("🙈 Oops!"),
            "Amounts can't be negative. Please try again.",
            Button("Back to the form", "setup_page")
        ])

    if student_name.strip() == "":
        state.student_name = "Friend"
    else:
        state.student_name = student_name.strip()
    state.monthly_income = monthly_income
    state.current_savings = current_savings
    state.savings_goal = savings_goal
    return expenses_page(state)


# =====================================
# ROUTE 4: EXPENSES HUB (no form here, so its buttons are safe navigation)
# =====================================

@route
def expenses_page(state: State) -> Page:
    """Shows the expenses added so far, with buttons for what to do next."""
    content = [
        Header("🧾 Your Monthly Expenses"),
        "Here's what you've added so far, " + state.student_name + ":",
        ""
    ]

    if len(state.expenses) > 0:
        for line in expense_chart_lines(state.expenses):
            content.append(line)
        content.append("")
        content.append("Total: " + money(total_expenses(state.expenses)))
    else:
        content.append("Nothing yet. Add your first expense!")

    content.extend([
        "",
        Button("Add an Expense ➕", "add_expense_page"),
        Button("Edit or Remove ✏️", "edit_page"),
        Button("Done: Show My Dashboard 📊", "dashboard")
    ])
    return Page(state, content)


# =====================================
# ROUTE 5 + 6: ADD AN EXPENSE
# =====================================

@route
def add_expense_page(state: State) -> Page:
    """Form for adding one expense."""
    return Page(state, [
        Header("➕ Add an Expense"),
        "Category:",
        SelectBox("category", CATEGORY_CHOICES),
        "Monthly cost ($):",
        TextBox("monthly_cost", "0.0"),
        CheckBox("is_essential", True),
        "↑ Checked = a NEED (rent, groceries). Unchecked = a WANT (fun stuff).",
        "Optional note (like 'Netflix + Spotify'):",
        TextArea("note", ""),
        "",
        Button("Save Expense ✅", "save_expense")
    ])


@route
def save_expense(state: State, category: str, monthly_cost: float,
                 is_essential: bool, note: str) -> Page:
    """Add a new expense to the list, or show an error if the cost is negative."""
    if monthly_cost < 0:
        return Page(state, [
            Header("🙈 Oops!"),
            "A cost can't be negative.",
            Button("Try Again", "add_expense_page")
        ])

    state.expenses.append(Expense(category, monthly_cost, is_essential, note.strip()))
    return expenses_page(state)


# =====================================
# ROUTE 7 + 8: EDIT OR REMOVE AN EXPENSE
# =====================================

@route
def edit_page(state: State) -> Page:
    """Form for changing the cost of an expense or deleting it."""
    if len(state.expenses) == 0:
        return Page(state, [
            Header("✏️ Edit Expenses"),
            "You haven't added any expenses yet.",
            Button("Add some", "add_expense_page")
        ])

    return Page(state, [
        Header("✏️ Edit Expenses"),
        "Which category do you want to change?",
        SelectBox("edit_category", unique_categories(state.expenses)),
        "New monthly cost ($):",
        TextBox("new_cost", "0.0"),
        CheckBox("remove_it", False),
        "↑ Check this to DELETE the expense instead.",
        "",
        Button("Save Changes", "save_edit")
    ])


@route
def save_edit(state: State, edit_category: str, new_cost: float, remove_it: bool) -> Page:
    """Update (or delete) the first expense in the chosen category."""
    position = find_expense_index(state.expenses, edit_category)

    if position == -1:
        return Page(state, [
            Header("🤔 Not found"),
            "We couldn't find that expense.",
            Button("Back", "edit_page")
        ])

    if remove_it:
        state.expenses.pop(position)
    elif new_cost < 0:
        return Page(state, [
            Header("🙈 Oops!"),
            "A cost can't be negative.",
            Button("Try Again", "edit_page")
        ])
    else:
        state.expenses[position].monthly_cost = new_cost

    return expenses_page(state)


# =====================================
# ROUTE 9: DASHBOARD
# =====================================

@route
def dashboard(state: State) -> Page:
    """The big summary: numbers, the budget diagram, and the goal timeline."""
    expense_total = total_expenses(state.expenses)
    needs = total_by_type(state.expenses, True)
    wants = total_by_type(state.expenses, False)
    saved_each_month = monthly_savings(state.monthly_income, expense_total)
    months = months_to_goal(state.current_savings, state.savings_goal, saved_each_month)

    content = [
        Header("📊 " + state.student_name + "'s Dashboard"),
        "Grade: " + budget_grade(state.monthly_income, expense_total),
        "",
        Header("The Big Picture", 2),
        "💵 Income: " + money(state.monthly_income),
        "🧾 Expenses: " + money(expense_total),
        "🏠 Needs: " + money(needs) + "   🎉 Wants: " + money(wants),
        "🐷 Recommended savings per month: " + money(saved_each_month),
        "",
        Header("Your Budget Breakdown", 2)
    ]
    content.extend(diagram_content(state))
    content.extend([
        "",
        Header("Savings Goal 🎯", 2),
        make_bar(state.current_savings, state.savings_goal, BAR_WIDTH) +
        "  " + money(state.current_savings) + " of " + money(state.savings_goal),
        goal_message(months),
        "",
        Button("Get Tips 💡", "tips_page"),
        Button("Edit My Expenses 🧾", "expenses_page"),
        Button("Change My Info 👤", "setup_page"),
        Button("Home 🏠", "index")
    ])
    return Page(state, content)


# =====================================
# ROUTE 10: TIPS
# =====================================

@route
def tips_page(state: State) -> Page:
    """Personalized money tips based on the student's numbers."""
    expense_total = total_expenses(state.expenses)
    wants = total_by_type(state.expenses, False)
    splurge = biggest_want(state.expenses)
    tips = []

    if expense_total > state.monthly_income:
        tips.append("🚨 You're spending more than you earn. Start by trimming your wants.")
    if splurge != "":
        tips.append("🎉 Your biggest 'want' is " + splurge + ". Cutting your wants by 20% would free up " +
                    money(wants * 0.20) + " a month.")
    if state.current_savings < state.monthly_income:
        tips.append("🛟 Aim for an emergency fund worth at least one month of income.")
    if len(tips) == 0:
        tips.append("🌟 Your budget looks great. Keep it up!")

    content = [Header("💡 Tips for " + state.student_name)]
    for tip in tips:
        content.append(tip)
    content.extend([
        "",
        Button("Back to Dashboard 📊", "dashboard"),
        Button("Home 🏠", "index")
    ])
    return Page(state, content)


# =====================================
# UNIT TESTS (assert_equal comes from Drafter)
# Route tests check the state each route changes. Routes that only read the state
# are tested by checking that the state is unchanged and the page has content.
# draw_budget_diagram and diagram_content draw pictures, so they can't be tested
# with assert_equal; the helpers that feed them are tested below.
# =====================================

def make_test_state() -> State:
    """Build a fresh State for tests (so tests never affect each other)."""
    return State("Sam", 1000.0, 100.0, 500.0, [])


def run_helper_tests() -> None:
    """Unit tests for every helper function."""
    mixed = [Expense("Rent/Housing", 400.0, True, ""),
             Expense("Eating Out", 100.0, False, "tacos"),
             Expense("Entertainment", 50.0, False, "")]
    assert_equal(money(1234.5), "$1,234.50")
    assert_equal(money(-5.0), "-$5.00")
    assert_equal(total_expenses(mixed), 550.0)
    assert_equal(total_expenses([]), 0.0)
    assert_equal(total_by_type(mixed, True), 400.0)
    assert_equal(total_by_type(mixed, False), 150.0)
    assert_equal(monthly_savings(1000.0, 600.0), 200.0)
    assert_equal(monthly_savings(500.0, 600.0), 0.0)
    assert_equal(months_to_goal(0.0, 1000.0, 250.0), 4)
    assert_equal(months_to_goal(0.0, 1001.0, 250.0), 5)
    assert_equal(months_to_goal(600.0, 500.0, 10.0), 0)
    assert_equal(months_to_goal(0.0, 100.0, 0.0), -1)
    assert_equal(budget_grade(1000.0, 400.0), "🤑 Superstar saver")
    assert_equal(budget_grade(1000.0, 600.0), "😎 Solid budget")
    assert_equal(budget_grade(1000.0, 900.0), "😬 Tight budget")
    assert_equal(budget_grade(1000.0, 1200.0), "🚨 Over budget")
    assert_equal(budget_grade(0.0, 10.0), "❓ Add your income to get a grade!")
    assert_equal(make_bar(5.0, 10.0, 10), "█████░░░░░")
    assert_equal(make_bar(5.0, 0.0, 4), "░░░░")
    assert_equal(unique_categories(mixed + [Expense("Eating Out", 5.0, False, "")]),
                 ["Rent/Housing", "Eating Out", "Entertainment"])
    assert_equal(find_expense_index(mixed, "Entertainment"), 2)
    assert_equal(find_expense_index(mixed, "Groceries"), -1)
    assert_equal(biggest_want(mixed), "Eating Out")
    assert_equal(biggest_want([]), "")
    assert_equal(expense_chart_lines([Expense("Eating Out", 100.0, False, "tacos")]),
                 ["████████████  🎉 Eating Out: $100.00  (tacos)"])
    assert_equal(goal_message(0), "🎉 You've already hit your savings goal!")
    assert_equal(goal_message(3), "⏳ About 3 month(s) until you reach your goal.")
    assert_equal(goal_message(-1), "🛑 No money is left to save yet. Try trimming a want or two.")
    assert_equal(get_cost(mixed[1]), 100.0)
    assert_equal(sort_expenses_by_cost(mixed)[0].category, "Rent/Housing")
    assert_equal(sort_expenses_by_cost(mixed)[2].category, "Entertainment")
    assert_equal(budget_slices(1000.0, mixed),
                 [("Needs", 400.0), ("Wants", 150.0), ("Savings", 225.0), ("Free to spend", 225.0)])
    assert_equal(budget_slices(100.0, mixed), [("Needs", 400.0), ("Wants", 150.0)])
    assert_equal(slice_text_lines([("Needs", 50.0), ("Wants", 50.0)]),
                 ["██████░░░░░░  Needs: $50.00 (50%)", "██████░░░░░░  Wants: $50.00 (50%)"])


def run_route_tests() -> None:
    """Unit tests for every route."""
    # index (read-only page)
    assert_equal(len(index(make_test_state()).content) > 0, True)

    # setup_page (read-only page)
    assert_equal(len(setup_page(make_test_state()).content) > 0, True)

    # save_setup: good input changes four fields
    state = make_test_state()
    save_setup(state, " Alex ", 1500.0, 50.0, 900.0)
    assert_equal(state.student_name, "Alex")
    assert_equal(state.monthly_income, 1500.0)
    assert_equal(state.current_savings, 50.0)
    assert_equal(state.savings_goal, 900.0)

    # save_setup: negative input changes nothing; blank name becomes "Friend"
    state = make_test_state()
    save_setup(state, "Alex", -5.0, 50.0, 900.0)
    assert_equal(state.student_name, "Sam")
    save_setup(state, "   ", 10.0, 0.0, 0.0)
    assert_equal(state.student_name, "Friend")

    # expenses_page (read-only page, with and without expenses)
    state = make_test_state()
    assert_equal(len(expenses_page(state).content) > 0, True)
    state.expenses.append(Expense("Groceries", 200.0, True, ""))
    assert_equal(len(expenses_page(state).content) > 0, True)

    # add_expense_page (read-only page)
    assert_equal(len(add_expense_page(make_test_state()).content) > 0, True)

    # save_expense: adds, and rejects negative costs
    state = make_test_state()
    save_expense(state, "Groceries", 200.0, True, " weekly shop ")
    assert_equal(len(state.expenses), 1)
    assert_equal(state.expenses[0], Expense("Groceries", 200.0, True, "weekly shop"))
    save_expense(state, "Groceries", -1.0, True, "")
    assert_equal(len(state.expenses), 1)

    # edit_page (read-only page, with and without expenses)
    state = make_test_state()
    assert_equal(len(edit_page(state).content) > 0, True)
    state.expenses.append(Expense("Groceries", 200.0, True, ""))
    assert_equal(len(edit_page(state).content) > 0, True)

    # save_edit: update, bad category, negative, and delete
    save_edit(state, "Groceries", 250.0, False)
    assert_equal(state.expenses[0].monthly_cost, 250.0)
    save_edit(state, "Nope", 10.0, False)
    assert_equal(len(state.expenses), 1)
    save_edit(state, "Groceries", -10.0, False)
    assert_equal(state.expenses[0].monthly_cost, 250.0)
    save_edit(state, "Groceries", 0.0, True)
    assert_equal(len(state.expenses), 0)

    # tips_page (read-only page: state must be unchanged)
    state = make_test_state()
    state.expenses.append(Expense("Eating Out", 1200.0, False, ""))
    assert_equal(len(tips_page(state).content) > 0, True)
    assert_equal(state, State("Sam", 1000.0, 100.0, 500.0, [Expense("Eating Out", 1200.0, False, "")]))


run_helper_tests()
run_route_tests()


# =====================================
# START WEBSITE
# =====================================

start_server(State("", 0.0, 0.0, 0.0, []), site_title="College Budget Buddy")
