import numpy as np
import plotly.graph_objects as go
from aerodynamic_model import (
    calculate_lift_coefficient,
    calculate_drag_coefficient,
    calculate_downforce,
    calculate_drag,
    calculate_efficiency,
)


def plot_downforce_vs_speed(air_density, wing_area, cl, current_speed_kmh):
    """
    Sweeps speed from 0 to 350 km/h and plots resulting downforce.
    Cl is held constant (i.e. current wing angle setting) - only speed changes.
    """
    speeds = np.linspace(0, 350, 100)
    downforces = [calculate_downforce(air_density, s, wing_area, cl) for s in speeds]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=speeds, y=downforces,
        mode="lines", name="Downforce",
        line=dict(color="#E10600", width=3)  # F1-red line
    ))

    # Mark the current speed setting with a vertical reference point
    current_downforce = calculate_downforce(air_density, current_speed_kmh, wing_area, cl)
    fig.add_trace(go.Scatter(
        x=[current_speed_kmh], y=[current_downforce],
        mode="markers", name="Current Setting",
        marker=dict(color="white", size=10, symbol="circle")
    ))

    fig.update_layout(
        title="Downforce vs Vehicle Speed",
        xaxis_title="Speed (km/h)",
        yaxis_title="Downforce (N)",
        template="plotly_dark",
        height=350,
    )
    return fig


def plot_drag_vs_speed(air_density, wing_area, cd, current_speed_kmh):
    """Same concept as above, but for drag."""
    speeds = np.linspace(0, 350, 100)
    drags = [calculate_drag(air_density, s, wing_area, cd) for s in speeds]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=speeds, y=drags,
        mode="lines", name="Drag",
        line=dict(color="#00A3E0", width=3)  # blue line, contrasts with red downforce line
    ))

    current_drag = calculate_drag(air_density, current_speed_kmh, wing_area, cd)
    fig.add_trace(go.Scatter(
        x=[current_speed_kmh], y=[current_drag],
        mode="markers", name="Current Setting",
        marker=dict(color="white", size=10, symbol="circle")
    ))

    fig.update_layout(
        title="Drag vs Vehicle Speed",
        xaxis_title="Speed (km/h)",
        yaxis_title="Drag (N)",
        template="plotly_dark",
        height=350,
    )
    return fig


def plot_downforce_drag_comparison(air_density, wing_area, cl, cd):
    """
    Plots downforce AND drag on the same axes across the speed range,
    so the user can visually compare the two curves and see the gap
    between them (roughly, the net aerodynamic benefit).
    """
    speeds = np.linspace(0, 350, 100)
    downforces = [calculate_downforce(air_density, s, wing_area, cl) for s in speeds]
    drags = [calculate_drag(air_density, s, wing_area, cd) for s in speeds]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=speeds, y=downforces, mode="lines", name="Downforce",
        line=dict(color="#E10600", width=3)
    ))
    fig.add_trace(go.Scatter(
        x=speeds, y=drags, mode="lines", name="Drag",
        line=dict(color="#00A3E0", width=3)
    ))

    fig.update_layout(
        title="Downforce vs Drag Comparison",
        xaxis_title="Speed (km/h)",
        yaxis_title="Force (N)",
        template="plotly_dark",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def plot_wing_angle_optimization(air_density, speed_kmh, wing_area, flap_angle, num_elements):
    """
    Sweeps wing ANGLE (not speed) from 0 to 45 degrees, holding speed constant,
    and shows how downforce, drag, and efficiency change.

    This reveals the classic F1 trade-off:
    - Max downforce angle is NOT the same as max efficiency angle
    - Beyond the stall angle, downforce actually drops
    """
    angles = np.linspace(0, 45, 100)
    downforces = []
    efficiencies = []

    for a in angles:
        cl = calculate_lift_coefficient(a, flap_angle, num_elements)
        cd = calculate_drag_coefficient(cl)
        df = calculate_downforce(air_density, speed_kmh, wing_area, cl)
        dr = calculate_drag(air_density, speed_kmh, wing_area, cd)
        eff = calculate_efficiency(df, dr)
        downforces.append(df)
        efficiencies.append(eff)

    # Find the angle that gives maximum downforce, and the angle that gives max efficiency
    best_downforce_angle = angles[np.argmax(downforces)]
    best_efficiency_angle = angles[np.argmax(efficiencies)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=angles, y=downforces, mode="lines", name="Downforce (N)",
        line=dict(color="#E10600", width=3), yaxis="y1"
    ))
    fig.add_trace(go.Scatter(
        x=angles, y=efficiencies, mode="lines", name="Efficiency (L/D)",
        line=dict(color="#FFD700", width=3, dash="dot"), yaxis="y2"
    ))

    # Vertical markers showing the optimum points
    fig.add_vline(x=best_downforce_angle, line_dash="dash", line_color="#E10600",
                   annotation_text="Max Downforce", annotation_position="top")
    fig.add_vline(x=best_efficiency_angle, line_dash="dash", line_color="#FFD700",
                   annotation_text="Max Efficiency", annotation_position="bottom")

    fig.update_layout(
        title="Wing Angle Optimization",
        xaxis_title="Wing Angle of Attack (°)",
        yaxis=dict(title="Downforce (N)", side="left"),
        yaxis2=dict(title="Efficiency (L/D)", overlaying="y", side="right"),
        template="plotly_dark",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def plot_wing_schematic(angle_of_attack_deg, flap_angle_deg, num_elements, speed_kmh):
    """
    Draws a simplified 2D side-profile schematic of the rear wing,
    tilted at the current angle of attack, with colored airflow arrows
    representing relative air speed over top vs bottom surfaces.
    """
    fig = go.Figure()

    angle_rad = np.radians(angle_of_attack_deg)

    # ---- Draw the main wing element as a simple curved airfoil shape ----
    # We build a basic cambered profile using a parametric curve, then rotate
    # it by the angle of attack so it visually tilts as the slider changes.
    chord = 3.0  # arbitrary drawing units, not meters - this is just a schematic
    x = np.linspace(0, chord, 60)
    thickness = 0.15 * chord * np.sin(np.pi * x / chord)  # simple symmetric thickness profile
    camber = 0.08 * chord * np.sin(np.pi * x / chord)      # simple camber (curvature)

    upper_y = camber + thickness
    lower_y = camber - thickness

    def rotate(px, py, angle):
        """Rotate a point (px, py) by 'angle' radians around the origin."""
        rx = px * np.cos(angle) + py * np.sin(angle)
        ry = -px * np.sin(angle) + py * np.cos(angle)
        return rx, ry

    upper_x_rot, upper_y_rot = rotate(x, upper_y, angle_rad)
    lower_x_rot, lower_y_rot = rotate(x, lower_y, angle_rad)

    # Draw main element (filled shape)
    fig.add_trace(go.Scatter(
        x=np.concatenate([upper_x_rot, lower_x_rot[::-1]]),
        y=np.concatenate([upper_y_rot, lower_y_rot[::-1]]),
        fill="toself",
        fillcolor="rgba(200,200,200,0.9)",
        line=dict(color="white", width=2),
        name="Main Element",
        showlegend=False,
    ))

    # ---- Draw additional flap elements behind the main plane ----
    flap_rad = np.radians(angle_of_attack_deg + flap_angle_deg)
    for i in range(1, num_elements):
        offset = i * chord * 0.55  # stagger each flap behind the previous one
        fx, fy = rotate(x * 0.6, (camber * 0.6 + thickness * 0.6), flap_rad)
        fig.add_trace(go.Scatter(
            x=fx + offset, y=fy - i * 0.15,
            fill="toself",
            fillcolor="rgba(225,6,0,0.75)",  # F1 red for flap elements
            line=dict(color="white", width=1.5),
            name=f"Flap {i}",
            showlegend=False,
        ))

    # ---- Airflow arrows ----
    # Speed factor scales arrow color/intensity with real vehicle speed
    speed_factor = min(speed_kmh / 350, 1.0)

    num_arrows = 6
    arrow_start_x = -1.0
    for i in range(num_arrows):
        y_level = -0.6 + i * 0.25

        # Arrows passing UNDER the wing (suction side for a rear wing) go faster
        # as angle of attack increases - represented with a color shift to red
        is_suction_side = y_level < 0.2
        local_speed = speed_factor * (1.3 if is_suction_side else 0.8)
        local_speed += (angle_of_attack_deg / 45) * 0.4 if is_suction_side else 0

        color = f"rgba({int(255*min(local_speed,1))}, {int(80*(1-min(local_speed,1)))}, {int(255*(1-min(local_speed,1)))}, 0.9)"

        fig.add_annotation(
            x=arrow_start_x + chord + 1.5, y=y_level,
            ax=arrow_start_x, ay=y_level,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True,
            arrowhead=3, arrowsize=1.5, arrowwidth=3,
            arrowcolor=color,
        )

    fig.update_layout(
        title=f"Rear Wing Side Profile — {angle_of_attack_deg}° Angle of Attack",
        template="plotly_dark",
        height=450,
        xaxis=dict(visible=False, range=[-2, 6]),
        yaxis=dict(visible=False, range=[-2, 2], scaleanchor="x", scaleratio=1),
        showlegend=False,
    )
    return fig