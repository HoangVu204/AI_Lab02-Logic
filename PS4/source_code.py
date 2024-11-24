import argparse
from typing import List, Tuple, Set
import os


class Clause:
    def __init__(self, literals: Set[str]):
        self.literals = literals

    @staticmethod
    def parse(clause_str: str) -> 'Clause':
        literals = set(clause_str.strip().split(' OR '))
        return Clause(literals)

    def negate(self) -> List['Clause']:
        negated_clauses = []
        for literal in self.literals:
            negated_literal = self.negate_literal(literal)
            negated_clause = Clause({negated_literal})
            negated_clauses.append(negated_clause)
        return negated_clauses

    @staticmethod
    def negate_literal(literal: str) -> str:
        return literal[1:] if literal.startswith('-') else '-' + literal

    def resolve(self, other: 'Clause') -> List['Clause']:
        resolvents = []
        for literal in self.literals:
            negated_literal = self.negate_literal(literal)
            if negated_literal in other.literals:
                new_literals = (
                    self.literals - {literal}) | (other.literals - {negated_literal})
                new_clause = Clause(new_literals)
                if not new_clause.contains_tautology():
                    resolvents.append(new_clause)
                    if not new_clause.literals:
                        return [new_clause]  # Return only the empty clause
        return resolvents

    def contains_tautology(self) -> bool:
        return any(self.negate_literal(literal) in self.literals for literal in self.literals)

    def __str__(self) -> str:
        def sort_key(literal: str) -> str:
            return literal.lstrip('-')

        sorted_literals = sorted(self.literals, key=sort_key)
        return ' OR '.join(sorted_literals) if self.literals else '{}'

    def __eq__(self, other) -> bool:
        return self.literals == other.literals

    def __hash__(self):
        return hash(frozenset(self.literals))


class KnowledgeBase:
    def __init__(self):
        self.clauses = []
        self.loop_count = 0

    def add_clause(self, clause: Clause):
        self.clauses.append(clause)

    def pl_resolution(self, alpha: Clause) -> Tuple[List[List[Clause]], bool]:
        negated_alpha_clauses = alpha.negate()
        for negated_clause in negated_alpha_clauses:
            self.add_clause(negated_clause)

        print("Knowledge Base after adding negation of alpha:")
        self.print_kb()

        all_clauses = self.clauses.copy()
        all_steps = []
        all_resolutions = []

        while True:
            self.loop_count += 1
            pairs = [(ci, cj) for i, ci in enumerate(all_clauses)
                     for j, cj in enumerate(all_clauses) if i < j]
            step_clauses = []

            for (clause1, clause2) in pairs:
                resolvents = clause1.resolve(clause2)
                for resolvent in resolvents:
                    all_resolutions.append((clause1, clause2, resolvent))
                    if not resolvent.literals:
                        step_clauses.append(resolvent)
                        all_steps.append(list(step_clauses))
                        self.print_resolutions(all_resolutions)
                        return all_steps, True, clause1, clause2  # Return the conflicting clauses
                    if resolvent not in all_clauses and resolvent not in step_clauses:
                        step_clauses.append(resolvent)

            if not step_clauses:
                if step_clauses:
                    all_steps.append(step_clauses)
                all_steps.append([])
                self.print_resolutions(all_resolutions)
                return all_steps, False, None, None

            step_clauses = sorted(set(step_clauses), key=lambda c: sorted(
                c.literals, key=lambda lit: lit.lstrip('-')))
            all_steps.append(step_clauses)
            all_clauses.extend(step_clauses)
            self.print_resolutions(all_resolutions)

    def print_kb(self):
        if not self.clauses:
            print("Knowledge Base is empty.")
            return

        for clause in self.clauses:
            print(str(clause))
        print("------")

    def print_resolutions(self, resolutions):
        print(f"Loop {self.loop_count}:")
        if not resolutions:
            print("No resolutions in this loop.")
        for (clause1, clause2, resolvent) in resolutions:
            print(f"Resolving: {clause1} with {clause2}")
            print(f"Result: {resolvent}")
        print("------")


def format_output(all_steps: List[List[Clause]], entails: bool, conflict_clauses: Tuple[Clause, Clause]) -> str:
    output_lines = []  # The output string will be constructed here

    def clause_sort_key(clause: Clause) -> list:
        return [lit.lstrip('-') for lit in sorted(clause.literals)]

    for step in all_steps:
        unique_clauses = sorted(set(step), key=lambda c: (
            len(c.literals), clause_sort_key(c)))
        output_lines.append(str(len(unique_clauses)))
        output_lines.extend(str(clause) for clause in unique_clauses)

    output_lines.append("YES" if entails else "NO")

    return '\n'.join(output_lines)


def parse_input(file_path: str) -> Tuple[Clause, List[Clause]]:
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            if len(lines) < 2:
                raise ValueError("Input file must contain at least two lines.")
            alpha = Clause.parse(lines[0].strip())
            n = int(lines[1].strip())
            if len(lines) < n + 2:
                raise ValueError("Input file does not contain enough clauses.")
            kb = [Clause.parse(lines[i + 2].strip()) for i in range(n)]
        return alpha, kb
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='PL Resolution to check if KB entails alpha.')
    parser.add_argument('-i', '--input_file', type=str,
                        help='Path to the input file')
    parser.add_argument('-o', '--output_file', type=str,
                        help='Path to the output file')
    parser.add_argument('-all', action='store_true',
                        help='Run all input files in the Input folder')

    args = parser.parse_args()

    if args.all:
        input_folder = 'Input'
        output_folder = 'Output'

        os.makedirs(output_folder, exist_ok=True)

        for i in range(1, 10):  # Process input01.txt to input09.txt
            input_file = os.path.join(input_folder, f'input0{i}.txt')
            output_file = os.path.join(output_folder, f'output0{i}.txt')

            if os.path.exists(input_file):
                alpha, clauses = parse_input(input_file)

                kb = KnowledgeBase()
                for clause in clauses:
                    kb.add_clause(clause)

                all_steps, entails, conflict_clause1, conflict_clause2 = kb.pl_resolution(
                    alpha)
                output = format_output(
                    all_steps, entails, (conflict_clause1, conflict_clause2))

                with open(output_file, 'w') as file:
                    file.write(output)

            else:
                print(f"Input file {input_file} does not exist.")

    elif args.input_file and args.output_file:
        alpha, clauses = parse_input(args.input_file)

        kb = KnowledgeBase()
        for clause in clauses:
            kb.add_clause(clause)

        all_steps, entails, conflict_clause1, conflict_clause2 = kb.pl_resolution(
            alpha)
        output = format_output(
            all_steps, entails, (conflict_clause1, conflict_clause2))

        with open(args.output_file, 'w') as file:
            file.write(output)

    else:
        print('Please provide a valid input file and output file.')


if __name__ == '__main__':
    main()
