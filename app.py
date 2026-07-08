import streamlit as st
import numpy as np
from aerodynamic_model import (
    calculate_wing_area,
    calculate_lift_coefficient,
    calculate_drag_coefficient,
    calculate_downforce,
    calculate_drag,
    newtons_to_kgf,
    calculate_efficiency,
    estimate_cornering_speed,
    estimate_lap_time_effect,
)
from visualization import (
    plot_downforce_vs_speed,
    plot_drag_vs_speed,
    plot_downforce_drag_comparison,
    plot_wing_angle_optimization,
    plot_wing_schematic,
)

# ----------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------
st.set_page_config(
    page_title="F1 Rear Wing Aerodynamics Simulator",
    page_icon="🏎️",
    layout="wide",  # uses the full browser width instead of a narrow centered column
)

# ----------------------------------------------------
# SESSION STATE (remembers DRS on/off between reruns)
# ----------------------------------------------------
if "drs_on" not in st.session_state:
    st.session_state.drs_on = False

if "saved_configs" not in st.session_state:
    st.session_state.saved_configs = []

# ----------------------------------------------------
# TITLE
# ----------------------------------------------------
st.title("🏎️ Formula 1 Rear Wing Aerodynamics Simulator")
st.caption("A simplified aerodynamic design and analysis tool inspired by F1 engineering software.")

# ----------------------------------------------------
# LAYOUT: three columns -> LEFT (inputs) | CENTER (visual) | RIGHT (results)
# ----------------------------------------------------
left_col, center_col, right_col = st.columns([1, 1.4, 1])

# ======================================================
# LEFT COLUMN: DESIGN PARAMETERS
# ======================================================
with left_col:
    st.header("Design Parameters")

    st.subheader("Wing Geometry")
    angle_of_attack = st.slider("Wing Angle of Attack (°)", min_value=0, max_value=45, value=12)
    chord_length = st.slider("Chord Length (m)", min_value=0.2, max_value=1.5, value=0.4, step=0.05)
    wing_span = st.slider("Wing Span (m)", min_value=0.8, max_value=2.0, value=1.6, step=0.05)
    num_elements = st.slider("Number of Wing Elements", min_value=1, max_value=4, value=2)
    flap_angle = st.slider("Flap Angle (°)", min_value=0, max_value=40, value=15)

    st.subheader("Vehicle Conditions")
    speed_kmh = st.slider("Vehicle Speed (km/h)", min_value=0, max_value=350, value=250)
    air_density = st.slider("Air Density (kg/m³)", min_value=1.0, max_value=1.3, value=1.225, step=0.005)

    st.subheader("Vehicle Parameters")
    car_mass = st.slider("Car Mass (kg)", min_value=700, max_value=900, value=798)
    tire_grip = st.slider("Tire Grip Coefficient", min_value=1.0, max_value=2.5, value=1.6, step=0.05)

    st.subheader("DRS (Drag Reduction System)")
    drs_button_label = "Turn DRS OFF" if st.session_state.drs_on else "Turn DRS ON"
    if st.button(drs_button_label):
        st.session_state.drs_on = not st.session_state.drs_on

    if st.session_state.drs_on:
        st.success("DRS: ACTIVE")
    else:
        st.info("DRS: INACTIVE")

# ----------------------------------------------------
# APPLY DRS EFFECT (reduces effective wing angle when active)
# ----------------------------------------------------
if st.session_state.drs_on:
    effective_angle = angle_of_attack * 0.3   # DRS flattens the wing, cutting effective angle drastically
    effective_flap = flap_angle * 0.3
else:
    effective_angle = angle_of_attack
    effective_flap = flap_angle

# ----------------------------------------------------
# RUN THE PHYSICS ENGINE
# ----------------------------------------------------
wing_area = calculate_wing_area(wing_span, chord_length)
cl = calculate_lift_coefficient(effective_angle, effective_flap, num_elements)
cd = calculate_drag_coefficient(cl)

downforce_n = calculate_downforce(air_density, speed_kmh, wing_area, cl)
drag_n = calculate_drag(air_density, speed_kmh, wing_area, cd)

downforce_kgf = newtons_to_kgf(downforce_n)
efficiency = calculate_efficiency(downforce_n, drag_n)
cornering_speed = estimate_cornering_speed(downforce_n, car_mass, tire_grip)

# Baseline (DRS off, same everything else) - used to show lap time DELTA
baseline_cl = calculate_lift_coefficient(angle_of_attack, flap_angle, num_elements)
baseline_cd = calculate_drag_coefficient(baseline_cl)
baseline_downforce = calculate_downforce(air_density, speed_kmh, wing_area, baseline_cl)
baseline_drag = calculate_drag(air_density, speed_kmh, wing_area, baseline_cd)
baseline_efficiency = calculate_efficiency(baseline_downforce, baseline_drag)

lap_time_delta = estimate_lap_time_effect(baseline_efficiency, efficiency)

# ----------------------------------------------------
# DRS ON vs OFF COMPARISON DATA (regardless of current toggle state)
# ----------------------------------------------------
drs_on_angle = angle_of_attack * 0.3
drs_on_flap = flap_angle * 0.3

drs_on_cl = calculate_lift_coefficient(drs_on_angle, drs_on_flap, num_elements)
drs_on_cd = calculate_drag_coefficient(drs_on_cl)
drs_on_downforce = calculate_downforce(air_density, speed_kmh, wing_area, drs_on_cl)
drs_on_drag = calculate_drag(air_density, speed_kmh, wing_area, drs_on_cd)
drs_on_efficiency = calculate_efficiency(drs_on_downforce, drs_on_drag)
drs_on_top_speed_gain_kmh = (baseline_drag - drs_on_drag) / baseline_drag * 15 if baseline_drag > 0 else 0

# ======================================================
# CENTER COLUMN: VISUALIZATION (placeholder for now - built in Step 6)
# ======================================================
with center_col:
    st.header("Wing Visualization")
    st.plotly_chart(
        plot_wing_schematic(effective_angle, effective_flap, num_elements, speed_kmh),
        use_container_width=True,
    )
    st.caption(
        "Simplified side-profile schematic. Red flap elements represent additional "
        "win surfaces; arrow color represents relative local airflow speed "
        "(blue = slower, red = faster), consistent with the pressure differences "
        "that generate downforce."
    )

# ======================================================
# RIGHT COLUMN: PERFORMANCE ANALYSIS
# ======================================================
with right_col:
    st.header("Performance Analysis")

    st.metric("Downforce", f"{downforce_n:,.0f} N", f"{downforce_kgf:,.0f} kgf")
    st.metric("Drag", f"{drag_n:,.0f} N")
    st.metric("Efficiency (L/D)", f"{efficiency:.2f}")
    st.metric("Cornering Speed", f"{cornering_speed:,.0f} km/h")
    st.metric("Lap Time Effect", f"{lap_time_delta:+.2f} s")

    st.caption(
        "Lap time effect is estimated relative to the same wing with DRS OFF, "
        "using a simplified efficiency-based approximation."
    )
# ======================================================
# PERFORMANCE GRAPHS SECTION (full width, below the 3 columns)
# ======================================================
st.markdown("---")
st.header("Performance Graphs")

graph_col1, graph_col2 = st.columns(2)

with graph_col1:
    st.plotly_chart(
        plot_downforce_vs_speed(air_density, wing_area, cl, speed_kmh),
        use_container_width=True,
    )
    st.caption(
        "Downforce grows with the SQUARE of speed. This is why aero effects are "
        "almost negligible in slow corners but dominant at high speed."
    )

with graph_col2:
    st.plotly_chart(
        plot_drag_vs_speed(air_density, wing_area, cd, speed_kmh),
        use_container_width=True,
    )
    st.caption(
        "Drag follows the same speed-squared relationship — this is the direct "
        "'cost' of the downforce being generated."
    )

st.plotly_chart(
    plot_downforce_drag_comparison(air_density, wing_area, cl, cd),
    use_container_width=True,
)
st.caption(
    "Comparing both curves together shows the trade-off directly: a wider gap "
    "between the red (downforce) and blue (drag) lines at your target speed "
    "generally indicates a more favorable aerodynamic trade-off."
)

st.plotly_chart(
    plot_wing_angle_optimization(air_density, speed_kmh, wing_area, flap_angle, num_elements),
    use_container_width=True,
)
st.caption(
    "This sweeps wing angle (at your current speed) to reveal that the angle "
    "giving MAXIMUM downforce is not the same as the angle giving MAXIMUM "
    "efficiency (L/D). Real F1 engineers must choose a compromise between these "
    "based on the specific circuit's characteristics (e.g. Monza favors "
    "efficiency; Monaco favors raw downforce)."
)
# ======================================================
# ADVANCED FEATURES SECTION
# ======================================================
st.markdown("---")
st.header("Advanced Tools")

tab1, tab2, tab3 = st.tabs(["DRS Comparison", "Saved Configurations", "Wing Angle Optimizer"])

# --------------------------------------------------
# TAB 1: DRS COMPARISON
# --------------------------------------------------
with tab1:
    st.subheader("DRS OFF vs DRS ON — Direct Comparison")
    st.caption("Calculated at your current wing angle, flap angle, and speed settings.")

    comp_col1, comp_col2 = st.columns(2)

    with comp_col1:
        st.markdown("**DRS OFF**")
        st.metric("Downforce", f"{baseline_downforce:,.0f} N")
        st.metric("Drag", f"{baseline_drag:,.0f} N")
        st.metric("Efficiency (L/D)", f"{baseline_efficiency:.2f}")

    with comp_col2:
        st.markdown("**DRS ON**")
        st.metric(
            "Downforce", f"{drs_on_downforce:,.0f} N",
            f"{drs_on_downforce - baseline_downforce:,.0f} N"
        )
        st.metric(
            "Drag", f"{drs_on_drag:,.0f} N",
            f"{drs_on_drag - baseline_drag:,.0f} N"
        )
        st.metric(
            "Efficiency (L/D)", f"{drs_on_efficiency:.2f}",
            f"{drs_on_efficiency - baseline_efficiency:.2f}"
        )

    st.info(
        f"Estimated straight-line speed gain from DRS: "
        f"**+{drs_on_top_speed_gain_kmh:.1f} km/h** (simplified estimate based on drag reduction)."
    )

# --------------------------------------------------
# TAB 2: SAVED CONFIGURATIONS
# --------------------------------------------------
with tab2:
    st.subheader("Save and Compare Wing Designs")

    config_name = st.text_input("Name this configuration", placeholder="e.g. Monza Low-Downforce")

    if st.button("💾 Save Current Configuration"):
        if config_name.strip() == "":
            st.warning("Please enter a name before saving.")
        else:
            st.session_state.saved_configs.append({
                "name": config_name,
                "angle": angle_of_attack,
                "flap_angle": flap_angle,
                "elements": num_elements,
                "speed": speed_kmh,
                "downforce": downforce_n,
                "drag": drag_n,
                "efficiency": efficiency,
            })
            st.success(f"Saved '{config_name}'")

    if len(st.session_state.saved_configs) == 0:
        st.write("No configurations saved yet. Adjust the sliders above and save your first design.")
    else:
        st.markdown("**Saved Configurations:**")
        for i, config in enumerate(st.session_state.saved_configs):
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
                c1.write(f"**{config['name']}**")
                c2.write(f"{config['angle']}°")
                c3.write(f"{config['downforce']:,.0f} N")
                c4.write(f"{config['efficiency']:.2f} L/D")
                if c5.button("Delete", key=f"delete_{i}"):
                    st.session_state.saved_configs.pop(i)
                    st.rerun()

# --------------------------------------------------
# TAB 3: WING ANGLE OPTIMIZER
# --------------------------------------------------
with tab3:
    st.subheader("Find the Optimal Wing Angle")
    st.caption("Sweeps wing angle at your current speed/flap/element settings to find the best angle for your chosen goal.")

    goal = st.radio(
        "Optimization Goal",
        ["Maximum Downforce", "Maximum Efficiency (L/D)"],
        horizontal=True,
    )

    if st.button("🔍 Run Optimization"):
        angles_sweep = np.linspace(0, 45, 200)
        results = []
        for a in angles_sweep:
            sweep_cl = calculate_lift_coefficient(a, flap_angle, num_elements)
            sweep_cd = calculate_drag_coefficient(sweep_cl)
            sweep_df = calculate_downforce(air_density, speed_kmh, wing_area, sweep_cl)
            sweep_dr = calculate_drag(air_density, speed_kmh, wing_area, sweep_cd)
            sweep_eff = calculate_efficiency(sweep_df, sweep_dr)
            results.append((a, sweep_df, sweep_dr, sweep_eff))

        if goal == "Maximum Downforce":
            best = max(results, key=lambda r: r[1])
            st.success(
                f"**Optimal angle: {best[0]:.1f}°** — produces {best[1]:,.0f} N downforce "
                f"(efficiency at this angle: {best[3]:.2f})"
            )
        else:
            best = max(results, key=lambda r: r[3])
            st.success(
                f"**Optimal angle: {best[0]:.1f}°** — produces {best[3]:.2f} L/D efficiency "
                f"(downforce at this angle: {best[1]:,.0f} N)"
            )