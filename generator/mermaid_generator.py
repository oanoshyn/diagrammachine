import os

import astroid
import click
from astroid import (
    AnnAssign,
    Assign,
    ClassDef,
    FunctionDef,
    ImportFrom,
    Name,
    Subscript,
)
from entities import Attribute, Function
from utils import _infer

diagram_template = """---
title: {name}
---
classDiagram
"""

class_definition_template = """
{connection_definitions}
class {class_name} {{ 
{attribute_definitions}
{method_definitions}
}}
"""


ClassName = str
ClassInfo = tuple[ClassName, list[Attribute], list[Function]]
Import = tuple[str, list[str]]


class AstMermaidGenerator:
    def __init__(self, title: str, target_path: str, project_absolute_path: str):
        """
        :param title: Title of the generated diagram
        :param target_path: File or directory that we want to generate the diagram for
        :param project_absolute_path: Used to build complete file path from python imports
        :param inheritance_depth: Specifies how deep we want to analyze parents
        """

        self.title = title
        self.target_path = target_path
        self.project_absolute_path = project_absolute_path

    def generate_diagram(self) -> str:
        """
        Generates a diagram from a collected ClassInfo objects
        """

        diagram = diagram_template
        diagram = diagram.format(name=self.title)

        classes_info = self._get_classes_info()
        for (
            class_name,
            class_parents,
            class_attributes,
            class_functions,
        ) in classes_info:
            class_definition = class_definition_template

            connection_definitions = ""
            for parent in class_parents:
                connection_definitions += f"{class_name} <|-- {parent}\n"

            attribute_definitions = ""
            for attribute in class_attributes:
                attribute_definitions += (
                    f"{attribute.name}: {attribute.type_annotation}\n"
                )

            function_definitions = ""
            for function in class_functions:
                function_definitions += f"{function.name}()\n"

            class_template = class_definition.format(
                class_name=class_name,
                attribute_definitions=attribute_definitions,
                method_definitions=function_definitions.strip(),
                connection_definitions=connection_definitions,
            )

            diagram += class_template

        return diagram

    def _get_classes_info(self) -> list[ClassInfo]:
        """
        Get ClassInfo objects from files
        """

        splited_files_path = self.target_path.split("++")

        class_info_objects = []

        if len(splited_files_path) > 1:
            for file_path in splited_files_path:
                # Only python files are analyzed
                if not file_path.endswith(".py"):
                    continue

                class_info_objects.extend(
                    self._collect_classes_info_from_file(file_path)
                )

        # if directory was passed - walk through all its files recursively
        elif os.path.isdir(self.target_path):
            for root, dirs, files in os.walk(self.target_path):
                for file in files:
                    file_path = os.path.join(root, file)

                    # Only python files are analyzed
                    if not file_path.endswith(".py"):
                        continue

                    class_info_objects.extend(
                        self._collect_classes_info_from_file(file_path)
                    )

        elif os.path.isfile(self.target_path):
            class_info_objects = self._collect_classes_info_from_file(self.target_path)

        return class_info_objects

    def _collect_classes_info_from_file(self, file_path) -> list[ClassInfo]:
        """
        Get ClassInfo objects for all classes present in the given file
        """

        if not os.path.isfile(file_path):
            raise ValueError(f"Not a valid {file_path=}")

        parsed_file = self.parse_file(file_path)

        (
            classes_info,
            classes_parents,
            imports,
        ) = self._extract_class_info_from_ast(parsed_file)

        # Extend with parents info
        classes_info.extend(
            self._get_parents_info_from_imports(classes_parents, imports)
        )

        return classes_info

    def _get_parents_info_from_imports(
        self, parents: list[ClassName], imports
    ) -> list[ClassInfo]:
        """
        Get ClassInfo objects for all classes from file's imports
        """

        parent_classes_info = []

        for import_module, import_names in imports:
            for import_name in import_names:
                if import_name in parents:
                    file_path = import_module.replace(".", "/")
                    absolute_file_path = f"{self.project_absolute_path}/{file_path}.py"

                    # Getting parents only from existing python files, not from python packages
                    try:
                        parsed_ast = self.parse_file(absolute_file_path)

                        if parsed_ast is None:
                            continue

                    except FileNotFoundError:
                        continue

                    class_info, _, _ = self._extract_class_info_from_ast(
                        parsed_ast, import_name
                    )
                    parent_classes_info.extend(class_info)

        return parent_classes_info

    def _extract_class_info_from_ast(
        self, parsed_ast, class_name: str | None = None
    ) -> tuple[list[ClassInfo], list[ClassName], list[Import]]:
        """
        Get ClassInfo objects from the parsed astroid ast

        `class_name` is needed when getting ClassInfo for a particular class(e.g. when parsing imports)
        """

        imports = []
        classes_info = []
        classes_parents = []

        # Collect imports to get parents information later on
        for node in parsed_ast.body:
            if isinstance(node, ImportFrom):
                import_module = str(node.modname)
                import_names = [import_name[0] for import_name in node.names]
                imports.append((import_module, import_names))

        for node in parsed_ast.body:
            if isinstance(node, ClassDef):
                name = node.name
                attributes = self.extract_instance_attributes(node)
                functions = []
                for body_node in node.body:
                    # Get class attributes
                    if isinstance(body_node, (Assign, AnnAssign)):
                        attributes.append(Attribute(body_node))

                    # Get the function name
                    elif isinstance(body_node, FunctionDef):
                        functions.append(Function(body_node))

                parents = []
                for parent in node.bases:
                    inferred_node = _infer(parent)
                    parents.append(inferred_node.name)

                class_info = name, parents, attributes, functions

                # If we found a class return the class info
                if class_name == name:
                    return [class_info], [], []

                classes_info.append(class_info)
                classes_parents.extend(parents)

        return classes_info, classes_parents, imports

    def extract_instance_attributes(self, class_node: ClassDef) -> list[Attribute]:
        """
        Get the list of class instance attributes
        """

        attributes = []
        for instance_attr in list(class_node.instance_attrs.values()):
            for attr in instance_attr:
                attributes.append(Attribute(attr))
        return attributes

    def parse_file(self, absolute_file_path: str):
        """
        Parse given file handle common errors and return
        """

        parsed_ast = None

        try:
            parsed_ast = astroid.parse(open(absolute_file_path, "r").read())

        except SyntaxError as err:
            # In case of a syntax error print the file name and error
            click.echo(message=f"Failed to parse {absolute_file_path}")

        return parsed_ast


@click.command()
@click.option("--title", default="Autogenerated diagram", help="Title of the diagram")
@click.option(
    "--path",
    help="Path to the directory or python file(s) that contains code to be visualized. "
    "When passing multiple files place ++ between the files path(e.g. path1++path2...)",
)
@click.option("--project_path", help="Path to the root directory of the project")
def main(title: str, path: str | list[str], project_path: str):
    gen = AstMermaidGenerator(
        title=title,
        target_path=path,
        project_absolute_path=project_path,
    )

    click.echo(gen.generate_diagram())


if __name__ == "__main__":
    main()
