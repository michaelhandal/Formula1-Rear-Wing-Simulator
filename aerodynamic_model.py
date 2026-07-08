import numpy as np

# ----------------------------------------------------
# CONSTANTS
# ----------------------------------------------------
GRAVITY = 9.81  # m/s^2, used to convert Newtons to kg-force


def kmh_to_ms(speed_kmh):
    """Convert speed from km/h to m/s, since our physics equations need m/s."""
    return speed_kmh / 3.6


def calculate_wing_area(span_m, chord_m):
    """
    Wing area = span x chord.
    span_m: the wing's width, left tip to right tip (meters)
    chord_m: the wing's depth, front edge to back edge (meters)
    """
    return span_m * chord_m


def calculate_lift_coefficient(angle_of_attack_deg, flap_angle_deg, num_elements, stall_angle_deg=35):
    """
    Estimate the lift (downforce) coefficient Cl based on wing angle.

    angle_of_attack_deg: main wing angle relative to airflow (degrees)
    flap_angle_deg: additional angle added by the flap(s)
    num_elements: number of wing elements (main plane + flaps) - more elements
                  allow higher effective angles before stalling, since each
                  element re-energizes the airflow for the next one
    stall_angle_deg: angle beyond which airflow separates and Cl drops sharply

    Returns Cl (dimensionless).
    """
    # Effective total angle seen by the airflow
    effective_angle = angle_of_attack_deg + (flap_angle_deg * 0.5)

    # Each extra element raises the practical stall angle a bit,
    # because multi-element wings delay flow separation
    adjusted_stall_angle = stall_angle_deg + (num_elements - 1) * 4

    if effective_angle <= adjusted_stall_angle:
        # Linear region: Cl grows steadily with angle
        # 0.11 per degree is a simplified but realistic slope for
        # multi-element F1-style wings
        cl = 0.11 * effective_angle * (1 + 0.15 * (num_elements - 1))
    else:
        # Post-stall: Cl drops off sharply (flow has separated)
        cl_at_stall = 0.11 * adjusted_stall_angle * (1 + 0.15 * (num_elements - 1))
        overshoot = effective_angle - adjusted_stall_angle
        cl = cl_at_stall - (0.05 * overshoot)
        cl = max(cl, 0)  # Cl can't sensibly go negative in this simplified model

    return cl


def calculate_drag_coefficient(cl, base_cd=0.05):
    """
    Estimate drag coefficient Cd using the induced drag relationship:
    drag grows with the SQUARE of lift/downforce (a real aerodynamic effect).

    base_cd: minimum drag from the wing's own shape/thickness, even at zero angle
    """
    induced_drag_factor = 0.10  # tunable constant representing wing efficiency
    cd = base_cd + (induced_drag_factor * cl**2)
    return cd


def calculate_downforce(air_density, speed_kmh, wing_area, cl):
    """
    Core downforce equation: F = 0.5 x rho x v^2 x A x Cl
    Returns downforce in Newtons.
    """
    v = kmh_to_ms(speed_kmh)
    downforce_n = 0.5 * air_density * (v ** 2) * wing_area * cl
    return downforce_n


def calculate_drag(air_density, speed_kmh, wing_area, cd):
    """
    Core drag equation: F = 0.5 x rho x v^2 x A x Cd
    Returns drag in Newtons.
    """
    v = kmh_to_ms(speed_kmh)
    drag_n = 0.5 * air_density * (v ** 2) * wing_area * cd
    return drag_n


def newtons_to_kgf(force_n):
    """Convert Newtons to kilograms-force, a more intuitive unit for many engineers."""
    return force_n / GRAVITY


def calculate_efficiency(downforce_n, drag_n):
    """
    Lift-to-drag ratio (L/D). Higher = more efficient wing
    (more downforce per unit of drag penalty).
    """
    if drag_n == 0:
        return 0
    return downforce_n / drag_n


def estimate_cornering_speed(downforce_n, car_mass_kg, tire_grip_coefficient, corner_radius_m=100):
    """
    Simplified cornering speed model using centripetal force balance:

    Required grip force = (mass x v^2) / radius
    Available grip force = tire_grip_coefficient x (weight + downforce)

    Setting them equal and solving for v gives max cornering speed.
    """
    weight_n = car_mass_kg * GRAVITY
    total_vertical_force = weight_n + downforce_n
    available_grip_n = tire_grip_coefficient * total_vertical_force

    # v = sqrt( (grip_force x radius) / mass )
    v_ms = np.sqrt((available_grip_n * corner_radius_m) / car_mass_kg)
    v_kmh = v_ms * 3.6
    return v_kmh


def estimate_lap_time_effect(baseline_efficiency, new_efficiency, baseline_laptime_s=90):
    """
    Very simplified estimate: assumes lap time scales inversely with
    aerodynamic efficiency (L/D). This is a rough approximation for
    demonstration purposes, not a real lap simulation.
    """
    if new_efficiency == 0:
        return 0
    ratio = baseline_efficiency / new_efficiency
    new_laptime = baseline_laptime_s * ratio
    return new_laptime - baseline_laptime_s