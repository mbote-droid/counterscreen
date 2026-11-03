"""Unit-tagged scalars, and the thermodynamic constants of [R21].

Every energy in this project carries its unit in its type. The reason is
`PROTOCOL.md` section 7.2: Rosetta's interface filter reports Rosetta Energy
Units, not kcal/mol, with no explicit solvent or conformational entropy
sampling. It may be ranked with and must never be quoted as an affinity, and
the phrase "REU-equivalent" is recorded there as an error made in v0.2. A bare
float cannot carry that distinction, so :class:`REU` and :class:`KcalPerMol`
are different types and **no conversion between them exists anywhere in this
package**. Writing that v0.2 sentence again is now a type error rather than a
style lapse.

The constants below are computed from the gas constant and the standard
temperature when this module is imported, rather than written down as
literals, so that the claim attached to [R21] in `REFERENCES.md` -- "Computed
directly, not recalled" -- stays true of the code as well as the prose.
"""

import math
from dataclasses import dataclass
from typing import ClassVar, Self, override


@dataclass(frozen=True, slots=True, order=True)
class Quantity:
    """A scalar that carries its unit in its type.

    Arithmetic is closed over a single unit: adding, subtracting and comparing
    are defined only between two quantities of the same type, and both mypy and
    the interpreter reject a mixture. Scaling takes a dimensionless factor, and
    dividing two quantities of one unit gives a dimensionless ratio.
    """

    value: float

    unit: ClassVar[str] = "dimensionless"

    def __post_init__(self) -> None:
        """Reject a non-finite value at construction rather than downstream."""
        if not math.isfinite(self.value):
            msg = f"{type(self).__name__} must be finite, got {self.value!r}"
            raise ValueError(msg)

    def __add__(self, other: Self) -> Self:
        """Add a quantity carrying the same unit.

        The runtime class check is not redundant with the annotation. mypy
        rejects ``REU(1) + KcalPerMol(1)`` statically, but a value arriving
        from parsed data or a registry lookup can defeat that, and duck typing
        would then add the two numbers silently. Returning ``NotImplemented``
        makes the interpreter raise.
        """
        if type(other) is not type(self):
            return NotImplemented
        return type(self)(self.value + other.value)

    def __sub__(self, other: Self) -> Self:
        """Subtract a quantity carrying the same unit."""
        if type(other) is not type(self):
            return NotImplemented
        return type(self)(self.value - other.value)

    def __neg__(self) -> Self:
        """Negate, keeping the unit."""
        return type(self)(-self.value)

    def __abs__(self) -> Self:
        """Absolute value, keeping the unit."""
        return type(self)(abs(self.value))

    def scaled_by(self, factor: float) -> Self:
        """Multiply by a dimensionless factor."""
        return type(self)(self.value * factor)

    def ratio_to(self, other: Self) -> float:
        """Divide by a quantity of the same unit, giving a dimensionless ratio."""
        if type(other) is not type(self):
            msg = f"cannot take a ratio between {type(self).unit} and {type(other).unit}"
            raise TypeError(msg)
        if other.value == 0.0:
            msg = f"cannot take a ratio to zero {type(self).unit}"
            raise ZeroDivisionError(msg)
        return self.value / other.value

    @override
    def __str__(self) -> str:
        """Render with the unit attached, so logs cannot drop it."""
        return f"{self.value:g} {type(self).unit}"


class Angstrom(Quantity):
    """A distance, in angstrom."""

    __slots__ = ()
    unit: ClassVar[str] = "Å"


class Kelvin(Quantity):
    """An absolute temperature, in kelvin."""

    __slots__ = ()
    unit: ClassVar[str] = "K"


class Molar(Quantity):
    """A concentration, in moles per litre."""

    __slots__ = ()
    unit: ClassVar[str] = "M"


class KcalPerMol(Quantity):
    """A free energy, in kilocalories per mole.

    This is a physical energy. A dissociation constant converts to one of these
    through :func:`delta_g_from_kd`, and back through :func:`kd_from_delta_g`.
    """

    __slots__ = ()
    unit: ClassVar[str] = "kcal/mol"


class REU(Quantity):
    """A Rosetta Energy Unit.

    Deliberately not convertible to :class:`KcalPerMol`. Rosetta's interface
    filter is historically named ``ddg`` and reports a score difference with no
    explicit solvent or conformational entropy sampling, so it ranks designs
    and does not measure affinity (`PROTOCOL.md` section 7.2). If a conversion
    ever appears to be needed, the need is a bug in the caller.
    """

    __slots__ = ()
    unit: ClassVar[str] = "REU"


# CODATA molar gas constant, 8.314462618 J/(mol K), expressed in kcal/(mol K)
# through the thermochemical calorie of exactly 4.184 J.
GAS_CONSTANT_KCAL_PER_MOL_K: float = 8.314462618 / 4184.0

#: Standard temperature used throughout, per [R21].
STANDARD_TEMPERATURE: Kelvin = Kelvin(298.15)

#: The 1 M standard state that makes the argument of the logarithm dimensionless.
STANDARD_STATE: Molar = Molar(1.0)

#: RT at the standard temperature. [R21] reports 0.5925 kcal/mol.
RT: KcalPerMol = KcalPerMol(GAS_CONSTANT_KCAL_PER_MOL_K * STANDARD_TEMPERATURE.value)

#: One decade of affinity. [R21] reports 1.3642 kcal/mol.
KCAL_PER_DECADE: KcalPerMol = KcalPerMol(RT.value * math.log(10.0))


def delta_g_from_kd(kd: Molar) -> KcalPerMol:
    """Convert a dissociation constant to a binding free energy.

    ``delta-G = RT * ln(K_D / C°)`` with ``C°`` the 1 M standard state, per
    [R21]. The standard state is explicit because ``RT * ln(K_D)`` alone takes
    the logarithm of a dimensioned quantity, which is what makes the shorthand
    in section 7.2 strictly wrong.
    """
    if kd.value <= 0.0:
        msg = f"a dissociation constant must be positive, got {kd}"
        raise ValueError(msg)
    return KcalPerMol(RT.value * math.log(kd.ratio_to(STANDARD_STATE)))


def kd_from_delta_g(delta_g: KcalPerMol) -> Molar:
    """Invert :func:`delta_g_from_kd`."""
    return Molar(math.exp(delta_g.ratio_to(RT)) * STANDARD_STATE.value)
