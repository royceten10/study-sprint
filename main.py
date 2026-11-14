"""Study Sprint: a homework tracker website built with Drafter.

Run this file in Thonny to launch the site locally.
"""
from dataclasses import dataclass
from typing import Any
from drafter import *

set_website_title("Study Sprint")
set_site_information(
    author="Royce Garrison (royceten@udel.edu)",
    description="A homework tracker that rewards you for finishing work, something I gotta do.",
    sources="Drafter documentation and help from Claude (LLM).",
    planning=["CS1 Final Project 0_ Pick a Problem.pdf", "CS1 Final Project 1_ Designs.pdf"],
    links=["https://github.com/royceten10/study-sprint"],
)
hide_debug_information()
set_website_framed(False)

# Global constants are allowed by the project rules.
PRIORITIES: list[str] = ["Low", "Medium", "High"]
MAX_TITLE_LENGTH: int = 40


@dataclass
class Assignment:
    """One homework item the student wants to track."""
    title: str
    course: str
    points: int
    priority: str
    done: bool


@dataclass
class State:
    """Everything the website remembers between pages."""
    student_name: str
    assignments: list[Assignment]
    points_earned: int
    message: str
    show_done: bool


# ---------------------------------------------------------------------
# Helper functions (these hold the logic so the routes stay short)
# ---------------------------------------------------------------------

def parse_points(text: str) -> int:
    """Turn text into a positive whole number, or return -1 if invalid."""
    cleaned = text.strip()
    if cleaned.isdigit() and int(cleaned) > 0:
        return int(cleaned)
    return -1


def find_index(assignments: list[Assignment], title: str) -> int:
    """Return the position of the assignment with this title, or -1."""
    for position in range(len(assignments)):
        if assignments[position].title == title:
            return position
    return -1


def pending_titles(assignments: list[Assignment]) -> list[str]:
    """Return the titles of every assignment that is not done yet."""
    titles = []
    for assignment in assignments:
        if not assignment.done:
            titles.append(assignment.title)
    return titles


def total_points(assignments: list[Assignment], done: bool) -> int:
    """Add up the points of assignments whose done flag matches."""
    total = 0
    for assignment in assignments:
        if assignment.done == done:
            total += assignment.points
    return total


def percent_done(assignments: list[Assignment]) -> int:
    """Return the percent of all tracked points that are finished."""
    earned = total_points(assignments, True)
    possible = earned + total_points(assignments, False)
    if possible == 0:
        return 0
    return round(earned / possible * 100)


def course_totals(assignments: list[Assignment]) -> dict[str, int]:
    """Return a dictionary of course name -> total points tracked."""
    totals: dict[str, int] = {}
    for assignment in assignments:
        if assignment.course not in totals:
            totals[assignment.course] = 0
        totals[assignment.course] += assignment.points
    return totals


def describe(assignment: Assignment) -> str:
    """Return a one-line summary of an assignment for the dashboard."""
    status = "[ ]"
    if assignment.done:
        status = "[x]"
    return (f"{status} {assignment.title} ({assignment.course}) - "
            f"{assignment.points} pts - {assignment.priority} priority")


def make_rows(state: State) -> list[str]:
    """Return dashboard lines, hiding finished work if the user chose to."""
    rows = []
    for assignment in state.assignments:
        if not assignment.done or state.show_done:
            rows.append(describe(assignment))
    return rows


def check_new_assignment(assignments: list[Assignment], title: str,
                         points_text: str) -> str:
    """Return an error message for bad form input, or '' if it is fine."""
    cleaned = title.strip()
    if cleaned == "":
        return "Please give the assignment a title."
    if len(cleaned) > MAX_TITLE_LENGTH:
        return f"Titles can be at most {MAX_TITLE_LENGTH} characters."
    if find_index(assignments, cleaned) != -1:
        return "You already have an assignment with that title."
    if parse_points(points_text) == -1:
        return "Points must be a whole number above zero."
    return ""


def add_form_page(state: State) -> Page:
    """Build the 'add assignment' page without changing the state."""
    content: list[Any] = [Header("Add an assignment", 2)]
    if state.message != "":
        content.append(state.message)
    content.extend([
        "Title:", TextBox("title", ""),
        "Course:", TextBox("course", ""),
        "Points:", TextBox("points", "10"),
        "Priority:", SelectBox("priority", PRIORITIES, "Medium"),
        Button("Save assignment", add_assignment),
        Button("Cancel", dashboard),
    ])
    return Page(state, content)


def complete_form_page(state: State) -> Page:
    """Build the 'mark complete' page without changing the state."""
    pending = pending_titles(state.assignments)
    content: list[Any] = [Header("Mark an assignment complete", 2)]
    if state.message != "":
        content.append(state.message)
    content.extend([
        "Which assignment did you finish?",
        SelectBox("title", pending, pending[0]),
        CheckBox("confirmed", False),
        "Check the box to confirm it is really finished.",
        Button("Complete it!", complete_assignment),
        Button("Cancel", dashboard),
    ])
    return Page(state, content)


# ---------------------------------------------------------------------
# Routes (the pages of the website)
# ---------------------------------------------------------------------

@route
def index(state: State) -> Page:
    """Welcome page that asks for the student's name."""
    content: list[Any] = [Header("Study Sprint", 1),
               "Track your homework and earn points as you finish it."]
    if state.message != "":
        content.append(state.message)
    content.extend([
        "What is your name?",
        TextBox("name", state.student_name),
        Button("Start", set_name),
    ])
    return Page(state, content)


@route
def set_name(state: State, name: str) -> Page:
    """Save the student's name, then go to the dashboard."""
    cleaned = name.strip()
    if cleaned == "":
        state.message = "Please enter a name to continue."
        return index(state)
    state.student_name = cleaned
    state.message = f"Welcome, {cleaned}!"
    return dashboard(state)


@route
def dashboard(state: State) -> Page:
    """Main page: shows every assignment and the student's points."""
    content: list[Any] = [Header(f"{state.student_name}'s Dashboard", 2)]
    if state.message != "":
        content.append(state.message)
    content.append(f"Points earned: {state.points_earned}")
    content.append("Points still to earn: "
                   f"{total_points(state.assignments, False)}")
    content.append(HorizontalRule())
    rows = make_rows(state)
    if len(rows) == 0:
        content.append("Nothing to show yet. Add an assignment!")
    for row in rows:
        content.append(row)
    content.append(HorizontalRule())
    toggle_label = "Hide completed"
    if not state.show_done:
        toggle_label = "Show completed"
    content.extend([
        Button("Add assignment", show_add_form),
        Button("Mark one complete", show_complete_form),
        Button(toggle_label, toggle_done),
        Button("Statistics", stats),
    ])
    return Page(state, content)


@route
def show_add_form(state: State) -> Page:
    """Clear old messages and show the add-assignment form."""
    state.message = ""
    return add_form_page(state)


@route
def add_assignment(state: State, title: str, course: str, points: str,
                   priority: str) -> Page:
    """Validate the form and add a new assignment to the state."""
    problem = check_new_assignment(state.assignments, title, points)
    if problem != "":
        state.message = problem
        return add_form_page(state)
    course_name = course.strip()
    if course_name == "":
        course_name = "General"
    state.assignments.append(Assignment(title.strip(), course_name,
                                        parse_points(points), priority,
                                        False))
    state.message = f"Added '{title.strip()}'."
    return dashboard(state)


@route
def show_complete_form(state: State) -> Page:
    """Show the complete-assignment form, if anything is left to do."""
    state.message = ""
    if len(pending_titles(state.assignments)) == 0:
        state.message = "Nothing is pending. Add an assignment first!"
        return dashboard(state)
    return complete_form_page(state)


@route
def complete_assignment(state: State, title: str, confirmed: bool) -> Page:
    """Mark an assignment done and award its points."""
    if not confirmed:
        state.message = "Please check the box to confirm."
        return complete_form_page(state)
    finished = state.assignments[find_index(state.assignments, title)]
    finished.done = True
    state.points_earned += finished.points
    state.message = f"Nice work! You earned {finished.points} points."
    return dashboard(state)


@route
def toggle_done(state: State) -> Page:
    """Flip whether finished assignments are visible on the dashboard."""
    state.show_done = not state.show_done
    state.message = ""
    return dashboard(state)


@route
def stats(state: State) -> Page:
    """Show overall progress and points tracked per course."""
    percent = percent_done(state.assignments)
    content: list[Any] = [Header("Statistics", 2),
               f"Overall progress: {percent}% of tracked points finished"]
    totals = course_totals(state.assignments)
    if len(totals) == 0:
        content.append("Add assignments to see course totals.")
    # .items() gives (key, value) pairs so we can loop over a dictionary.
    for course, points in totals.items():
        content.append(f"{course}: {points} points tracked")
    content.append(Button("Back to dashboard", dashboard))
    return Page(state, content)


# ---------------------------------------------------------------------
# Unit tests (run automatically when the program starts)
# ---------------------------------------------------------------------

def sample_state() -> State:
    """Build a fresh state with two assignments for the tests."""
    return State("Sam", [
        Assignment("Lab 1", "CS", 10, "High", False),
        Assignment("Essay", "English", 20, "Low", True),
    ], 20, "", True)


# helpers
assert_equal(parse_points(" 15 "), 15)
assert_equal(parse_points("abc"), -1)
assert_equal(parse_points("0"), -1)
assert_equal(find_index(sample_state().assignments, "Essay"), 1)
assert_equal(find_index(sample_state().assignments, "Nope"), -1)
assert_equal(pending_titles(sample_state().assignments), ["Lab 1"])
assert_equal(total_points(sample_state().assignments, True), 20)
assert_equal(percent_done(sample_state().assignments), 67)
assert_equal(percent_done([]), 0)
assert_equal(course_totals(sample_state().assignments),
             {"CS": 10, "English": 20})
assert_equal(describe(sample_state().assignments[0]),
             "[ ] Lab 1 (CS) - 10 pts - High priority")
assert_equal(len(make_rows(sample_state())), 2)
assert_equal(check_new_assignment([], "", "5"),
             "Please give the assignment a title.")
assert_equal(check_new_assignment([], "Quiz", "five"),
             "Points must be a whole number above zero.")
assert_equal(check_new_assignment([], "Quiz", "5"), "")

# routes (we check the state inside the Page that each route returns)
assert_equal(set_name(State("", [], 0, "", True), "Sam").state.student_name,
             "Sam")
assert_equal(set_name(State("", [], 0, "", True), "  ").state.message,
             "Please enter a name to continue.")
assert_equal(add_assignment(State("Sam", [], 0, "", True), "Lab 1", "CS",
                            "10", "High").state.assignments,
             [Assignment("Lab 1", "CS", 10, "High", False)])
assert_equal(add_assignment(State("Sam", [], 0, "", True), "", "CS",
                            "10", "High").state.assignments, [])
assert_equal(complete_assignment(sample_state(), "Lab 1",
                                 True).state.points_earned, 30)
assert_equal(complete_assignment(sample_state(), "Lab 1",
                                 False).state.points_earned, 20)
assert_equal(toggle_done(sample_state()).state.show_done, False)
assert_equal(show_complete_form(State("Sam", [], 0, "", True)).state.message,
             "Nothing is pending. Add an assignment first!")
assert_equal(show_add_form(sample_state()).state.message, "")
assert_equal(stats(sample_state()).state.points_earned, 20)
assert_equal(dashboard(sample_state()).state.student_name, "Sam")
assert_equal(index(sample_state()).state.student_name, "Sam")

start_server(State("", [], 0, "", True))
