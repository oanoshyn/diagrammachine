from _ast import Constant

from astroid import (
    AnnAssign,
    Assign,
    AssignAttr,
    BinOp,
    Call,
    ClassDef,
    Dict,
    FunctionDef,
    List,
    Name,
    Set,
    Subscript,
    Tuple,
)
from utils import _infer, default_return


class Attribute:
    """
    This entity represents a class attribute from python ast

    Attributes can be of two types:
        1) Assign, when attribute has a value assigned but does not have a type annotation
        2) AnnAssign, when attribute has both value and type annotation
    """

    def __init__(self, attribute_node: AnnAssign | Assign | AssignAttr):
        self.attribute_node = attribute_node

    @property
    @default_return(default_value="")
    def name(self) -> str:
        """
        Get the name of the attribute from ast node

        Depending on the attribute type we have to handle them separately since they have different
        structure

        All exceptions are handled by default_return decorator returning a default value
        """

        match self.attribute_node:
            # Attribute with a value and no type annotation
            case self.attribute_node if isinstance(self.attribute_node, Assign):
                return self.attribute_node.targets[0].name

            # Attribute with value and type annotation
            case self.attribute_node if isinstance(self.attribute_node, AnnAssign):
                return self.attribute_node.target.name

            case self.attribute_node if isinstance(self.attribute_node, AssignAttr):
                return self.attribute_node.attrname

    @property
    @default_return(default_value="")
    def type_annotation(self) -> str:
        """
        Get the type annotation of the attribute from ast node

        Depending on the attribute type we have to handle them separately since they have different
        structure

        All exceptions are handled by default_return decorator returning a default value
        """

        match self.attribute_node:
            # Attribute with a value and no type annotation
            case self.attribute_node if isinstance(self.attribute_node, Assign):
                return self._extract_type_from_Assign_node()

            # Attribute with value and type annotation
            case self.attribute_node if isinstance(self.attribute_node, AnnAssign):
                return self._extract_type_from_AnnAssign_node()

            # Instance attribute
            case self.attribute_node if isinstance(self.attribute_node, AssignAttr):
                return self._extract_type_from_AssignAttr()

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
            attribute_type = attribute_node_value.func.name

        return attribute_type

    def _extract_type_from_AnnAssign_node(self) -> str:
        """
        Get the type annotation from the attribute node of type AnnAssign

        Three options are handled:
            1) Subscript when the type annotation has parameters enclosed in square brackets
            2) When attribute has `simple` type annotation (e.g. attr1: str = 1)
            3) BinOp when attribute has type union as annotation (e.g. attr1: str | int)
        """

        attribute_node_annotation = self.attribute_node.annotation

        if isinstance(attribute_node_annotation, Name):
            return attribute_node_annotation.name

        if isinstance(attribute_node_annotation, (Subscript, BinOp)):
            return attribute_node_annotation.as_string()

        inferred_node = _infer(attribute_node_annotation)
        if isinstance(inferred_node, ClassDef):
            annotation_label = inferred_node.name
            if inferred_node.type_params:
                class_type_parameters = [
                    param.name.name for param in inferred_node.type_params
                ]
                return annotation_label + "[" + ", ".join(class_type_parameters) + "]"

            return annotation_label

        return ""

    def _extract_type_from_AssignAttr(self) -> str:
        """"""

        assert isinstance(self.attribute_node, AssignAttr)

        if isinstance(self.attribute_node.parent, AnnAssign):
            self.attribute_node = self.attribute_node.parent
            return self._extract_type_from_AnnAssign_node()

        return ""


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
