"""
Orion ODA v4.0 - Computed Property Decorator
=============================================

Provides computed property support for OntologyObjects with:
- Automatic caching of computed values
- Dependency tracking for cache invalidation
- Integration with Pydantic models

Palantir Pattern:
- Computed properties are derived from source properties
- Changes to dependencies invalidate the computed cache
- Computed values are not persisted but recalculated on access

Example:
    ```python
    class User(OntologyObject, ComputedPropertyMixin):
        first_name: str
        last_name: str

        @computed_property(depends_on=["first_name", "last_name"])
        def full_name(self) -> str:
            return f"{self.first_name} {self.last_name}"
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import functools
import weakref
from datetime import datetime, timezone
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

from pydantic import ConfigDict


T = TypeVar("T")
R = TypeVar("R")


# =============================================================================
# COMPUTED PROPERTY DESCRIPTOR
# =============================================================================


class ComputedPropertyDescriptor(Generic[T, R]):
    """
    Descriptor for computed properties with caching and dependency tracking.

    Attributes:
        func: The compute function
        depends_on: List of property names this computed property depends on
        cache_key: Key used to store cached value on instance
        cached: Whether to cache the computed value
    """

    def __init__(
        self,
        func: Callable[[T], R],
        depends_on: Optional[List[str]] = None,
        cached: bool = True,
    ) -> None:
        """
        Initialize the computed property descriptor.

        Args:
            func: Function to compute the property value
            depends_on: List of property names that trigger cache invalidation
            cached: Whether to cache computed values (default True)
        """
        self.func = func
        self.depends_on = depends_on or []
        self.cached = cached
        self.cache_key = f"_computed_cache_{func.__name__}"
        self.timestamp_key = f"_computed_ts_{func.__name__}"

        # Preserve function metadata
        functools.update_wrapper(self, func)

    def __set_name__(self, owner: Type[T], name: str) -> None:
        """Store the property name when attached to a class."""
        self.name = name
        self.cache_key = f"_computed_cache_{name}"
        self.timestamp_key = f"_computed_ts_{name}"

        # Register this computed property with the class
        if not hasattr(owner, "_computed_properties"):
            owner._computed_properties = {}
        owner._computed_properties[name] = self

        # Build reverse dependency map
        if not hasattr(owner, "_dependency_map"):
            owner._dependency_map = {}
        for dep in self.depends_on:
            if dep not in owner._dependency_map:
                owner._dependency_map[dep] = set()
            owner._dependency_map[dep].add(name)

    def __get__(self, obj: Optional[T], objtype: Optional[Type[T]] = None) -> R:
        """
        Get the computed property value.

        Returns cached value if available and dependencies unchanged,
        otherwise computes and caches the new value.
        """
        if obj is None:
            return self  # type: ignore

        # Check cache if caching is enabled
        if self.cached:
            cached_value = getattr(obj, self.cache_key, None)
            if cached_value is not None:
                return cached_value

        # Compute the value
        value = self.func(obj)

        # Cache the result
        if self.cached:
            object.__setattr__(obj, self.cache_key, value)
            object.__setattr__(obj, self.timestamp_key, datetime.now(timezone.utc))

        return value

    def invalidate(self, obj: T) -> None:
        """Invalidate the cached value for an instance."""
        if hasattr(obj, self.cache_key):
            object.__setattr__(obj, self.cache_key, None)
        if hasattr(obj, self.timestamp_key):
            object.__setattr__(obj, self.timestamp_key, None)

    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return self.depends_on.copy()


# =============================================================================
# DECORATOR FUNCTIONS
# =============================================================================


def computed_property(
    depends_on: Optional[List[str]] = None,
    cached: bool = True,
) -> Callable[[Callable[[T], R]], ComputedPropertyDescriptor[T, R]]:
    """
    Decorator to create a computed property with dependency tracking.

    Args:
        depends_on: List of property names that trigger cache invalidation
        cached: Whether to cache computed values (default True)

    Returns:
        Decorator function that creates a ComputedPropertyDescriptor

    Example:
        ```python
        class Order(OntologyObject, ComputedPropertyMixin):
            quantity: int
            unit_price: float
            tax_rate: float = 0.1

            @computed_property(depends_on=["quantity", "unit_price"])
            def subtotal(self) -> float:
                return self.quantity * self.unit_price

            @computed_property(depends_on=["subtotal", "tax_rate"])
            def total(self) -> float:
                return self.subtotal * (1 + self.tax_rate)
        ```
    """
    def decorator(func: Callable[[T], R]) -> ComputedPropertyDescriptor[T, R]:
        return ComputedPropertyDescriptor(func, depends_on=depends_on, cached=cached)
    return decorator


def cached_computed(func: Callable[[T], R]) -> ComputedPropertyDescriptor[T, R]:
    """
    Simple decorator for cached computed properties without explicit dependencies.

    The property will be computed once and cached until explicitly invalidated.

    Example:
        ```python
        class Report(OntologyObject, ComputedPropertyMixin):
            data: List[float]

            @cached_computed
            def average(self) -> float:
                return sum(self.data) / len(self.data) if self.data else 0.0
        ```
    """
    return ComputedPropertyDescriptor(func, depends_on=[], cached=True)


def invalidate_computed(obj: Any, property_name: str) -> None:
    """
    Manually invalidate a computed property's cache.

    Args:
        obj: The object instance
        property_name: Name of the computed property to invalidate

    Raises:
        ValueError: If property_name is not a computed property
    """
    computed_props = getattr(obj.__class__, "_computed_properties", {})
    descriptor = computed_props.get(property_name)

    if descriptor is None:
        raise ValueError(
            f"'{property_name}' is not a computed property on {obj.__class__.__name__}"
        )

    descriptor.invalidate(obj)


# =============================================================================
# COMPUTED PROPERTY MIXIN
# =============================================================================


class ComputedPropertyMixin:
    """
    Mixin class that provides automatic cache invalidation on property changes.

    When a property that is a dependency of a computed property changes,
    the computed property's cache is automatically invalidated.

    Works with Pydantic models through model_validator or __setattr__ override.

    Example:
        ```python
        class Product(OntologyObject, ComputedPropertyMixin):
            name: str
            price: float
            discount_percent: float = 0.0

            @computed_property(depends_on=["price", "discount_percent"])
            def final_price(self) -> float:
                return self.price * (1 - self.discount_percent / 100)
        ```
    """

    _computed_properties: Dict[str, ComputedPropertyDescriptor] = {}
    _dependency_map: Dict[str, Set[str]] = {}
    model_config = ConfigDict(ignored_types=(ComputedPropertyDescriptor,))

    def __setattr__(self, name: str, value: Any) -> None:
        """Override setattr to invalidate computed property caches."""
        # First, set the value
        super().__setattr__(name, value)

        # Then check if we need to invalidate any computed properties
        dependency_map = getattr(self.__class__, "_dependency_map", {})
        computed_props = getattr(self.__class__, "_computed_properties", {})

        if name in dependency_map:
            for computed_name in dependency_map[name]:
                descriptor = computed_props.get(computed_name)
                if descriptor:
                    descriptor.invalidate(self)

    def invalidate_all_computed(self) -> None:
        """Invalidate all computed property caches on this instance."""
        computed_props = getattr(self.__class__, "_computed_properties", {})
        for descriptor in computed_props.values():
            descriptor.invalidate(self)

    def get_computed_properties(self) -> Dict[str, Any]:
        """Get all computed property values as a dictionary."""
        computed_props = getattr(self.__class__, "_computed_properties", {})
        return {
            name: getattr(self, name)
            for name in computed_props
        }

    def get_computed_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata about computed properties."""
        computed_props = getattr(self.__class__, "_computed_properties", {})
        result = {}

        for name, descriptor in computed_props.items():
            cached_value = getattr(self, descriptor.cache_key, None)
            timestamp = getattr(self, descriptor.timestamp_key, None)

            result[name] = {
                "dependencies": descriptor.dependencies,
                "is_cached": cached_value is not None,
                "cached_at": timestamp.isoformat() if timestamp else None,
                "cached_value": cached_value,
            }

        return result


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_computed_dependencies(cls: Type) -> Dict[str, List[str]]:
    """
    Get the dependency graph for all computed properties in a class.

    Args:
        cls: The class to analyze

    Returns:
        Dict mapping computed property names to their dependencies
    """
    computed_props = getattr(cls, "_computed_properties", {})
    return {
        name: descriptor.dependencies
        for name, descriptor in computed_props.items()
    }


def get_dependents(cls: Type, property_name: str) -> Set[str]:
    """
    Get all computed properties that depend on a given property.

    Args:
        cls: The class to analyze
        property_name: The property name to find dependents for

    Returns:
        Set of computed property names that depend on the given property
    """
    dependency_map = getattr(cls, "_dependency_map", {})
    return dependency_map.get(property_name, set()).copy()


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Descriptor
    "ComputedPropertyDescriptor",
    # Decorators
    "computed_property",
    "cached_computed",
    "invalidate_computed",
    # Mixin
    "ComputedPropertyMixin",
    # Utilities
    "get_computed_dependencies",
    "get_dependents",
]
