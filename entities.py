from _ast import (
    AnnAssign,
    Assign,
    Constant,
    Subscript,
    Name,
    BinOp,
    FunctionDef,
    Set,
    Dict,
    List,
    Tuple,
    Call,
)


class Attribute:
    """
    This entity represents a class attribute from python ast

    Attributes can be of two types:
        1) Assign, when attribute has a value assigned but does not have a type annotation
        2) AnnAssign, when attribute has both value and type annotation
    """

    def __init__(self, attribute_node: AnnAssign | Assign):
        self.attribute_node = attribute_node

    @property
    def name(self) -> str:
        """
        Get the name of the attribute from ast node

        Depending on the attribute type we have to handle them separately since they have different
        structure
        """

        match self.attribute_node:
            # Attribute with a value and no type annotation
            case self.attribute_node if isinstance(self.attribute_node, Assign):
                return self.attribute_node.targets[0].id

            # Attribute with value and type annotation
            case self.attribute_node if isinstance(self.attribute_node, AnnAssign):
                return self.attribute_node.target.id

        return ""

    @property
    def type_annotation(self) -> str:
        """
        Get the type annotation of the attribute from ast node

        Depending on the attribute type we have to handle them separately since they have different
        structure
        """

        match self.attribute_node:
            # Attribute with a value and no type annotation
            case self.attribute_node if isinstance(self.attribute_node, Assign):
                return self._extract_type_from_Assign_node()

            # Attribute with value and type annotation
            case self.attribute_node if isinstance(self.attribute_node, AnnAssign):
                return self._extract_type_from_AnnAssign_node()

        return ""

    def _extract_type_from_Assign_node(self) -> str:
        """
        Get the type annotation from the attribute node of type Assign

        Three options are handled:
            1) Constant that just holds a specific value (e.g. attr1 = 1)
            2) Collection of Constants (e.g attr1 = [1,2,3,4])
            3) Call object (e.g. attr1 = list({1,2,3,4} or attr1 = SomeObject(param)))

        Unhandled options are just ignored and empty string type is returned
        """

        attribute_type = ""

        attribute_node_value = self.attribute_node.value

        if isinstance(attribute_node_value, Constant):
            attribute_type = type(attribute_node_value.value).__name__
        elif isinstance(attribute_node_value, (List, Dict, Set, Tuple)):
            # We cast to lower since the ast types for the collections are uppercase
            attribute_type = type(attribute_node_value).__name__.lower()
        elif isinstance(self.attribute_node.value, Call):
            attribute_type = attribute_node_value.func.id

        return attribute_type

    def _extract_type_from_AnnAssign_node(self) -> str:
        """
        Get the type annotation from the attribute node of type AnnAssign

        Three options are handled:
            1) Subscript when the type annotation has parameters enclosed in square brackets
            2) When attribute has `simple` type annotation (e.g. attr1: str = 1)
            3) BinOp when attribute has type union as annotation (e.g. attr1: str | int)
        """

        # For Subscript types (e.g. dict[str, Any]) get the type without parameters
        # dict[str, Any] -> dict
        attribute_type = ""
        if isinstance(self.attribute_node.annotation, Subscript):
            if isinstance(self.attribute_node.value, Name):
                attribute_type = self.attribute_node.value.id
            if isinstance(self.attribute_node.annotation.value, Name):
                attribute_type = self.attribute_node.annotation.value.id

        # For attributes that have annotations only get the type name
        elif isinstance(self.attribute_node.annotation, Name):
            attribute_type = self.attribute_node.annotation.id

        # For union types(e.g. <type> | <type> | <type> |...) get first two members
        # This can be improved to handle more union members
        elif isinstance(self.attribute_node.annotation, BinOp):
            left_type = self.attribute_node.annotation.left
            right_type = self.attribute_node.annotation.right

            if isinstance(left_type, Name):
                left_type = left_type.id
            elif isinstance(left_type, Constant):
                left_type = left_type.value

            if isinstance(right_type, Name):
                right_type = right_type.id
            elif isinstance(right_type, Constant):
                right_type = right_type.value
            attribute_type = f"{left_type} | {right_type}"

        return attribute_type


class Function:
    """
    This entity represents a class function from python ast
    """

    def __init__(self, function_node: FunctionDef):
        self.function_node = function_node

    @property
    def name(self) -> str:
        """
        Get the name of the function from ast function_node
        """

        return self.function_node.name
