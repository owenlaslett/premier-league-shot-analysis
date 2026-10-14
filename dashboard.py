    # Plot other shots
    pitch.scatter( # plots circles on the pitch
        [float(shot["X"]) * 120 for shot in misses], # Multiplying by 120 allows convertion from Understat shot coordinates to StatsBomb pitch representation
        [80 - float(shot["Y"]) * 80 for shot in misses], # Subtraction needed as the shot map was initially mirrored
        s=[25 + float(shot["xG"]) * 100 for shot in misses], # s controls the area of each circle, with s = 80+ 650(xG)
        color="white",
        edgecolors="black",
        ax=ax,
        zorder=3
    )

    # Plot goals
    pitch.scatter(
        [float(shot["X"]) * 120 for shot in goals],
        [80 - float(shot["Y"]) * 80 for shot in goals],
        s=[25 + float(shot["xG"]) * 100 for shot in goals],
        color="red",
        edgecolors="white",
        ax=ax,
        zorder=3
    )

    # Add a legend
    legend_elements = [
        Line2D([0], [0], marker="o", color="none", # Creates custom legend symbols, o creates a circular symbol
            markerfacecolor="red", markeredgecolor="white", # markerface and markeredge control colour
            markersize=10, label="Goal"),
        Line2D([0], [0], marker="o", color="none",
            markerfacecolor="white", markeredgecolor="black",
            markersize=10, label="Miss")
    ]
    goal_legend = ax.legend(
        handles=legend_elements,
        loc="lower left", # Places legend in top corner
        facecolor="#101820",
        labelcolor="white",
        edgecolor="white" ,
        fontsize= 11,
        prop={"family": "DejaVu Sans", "size":11}, # Font type
        handlelength=0.8, # Reduces the space allocated to circles
        handletextpad=0.3 # Reduces the gap between each circle and its text
    )

    # Keep first legend visible
    ax.add_artist(goal_legend) # Tells matplotlib to keep original legend
    xg_values = [0.05, 0.30, 0.70] # Choose which chance-quality value appear in the legend
    xg_handles = [
        Line2D(
            [0], [0],
            marker="o",
            linestyle="None",
            markerfacecolor="white",
            markeredgecolor="black",
            markersize=(25 + xg * 100) ** 0.5, # Makes legend circles match the shot-size formula, then square rooted
            label=f"{xg:.2f} xG"
        )
        for xg in xg_values
    ]
    ax.legend(
        handles=xg_handles,
        loc="lower right",
        facecolor="#101820",
        labelcolor="white",
        edgecolor="white",
        prop={"family": "DejaVu Sans", "size": 11},
        handlelength=0.8,
        handletextpad=0.3
    )

    # Display the pitch inside Streamlit
    st.pyplot(fig, use_container_width=True)

    # Close the Matplotlib figure to free memory
    plt.close(fig)

# Choose which type of analysis to display
mode = st.radio(
    "Analysis Mode:",
    ["Single Player", "Compare Players"],
    horizontal=True
)

if mode == "Single Player":
    name, player_id, season = select_player("single")
    shots = load_shots(player_id, season)
    left_panel, right_panel = st.columns([1, 1.3])
    with left_panel:
        st.subheader(name)
        show_statistics(shots)
    with right_panel:
        st.subheader("Player Shot Map")
        show_shot_map(shots)
else:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Player 1")
        name1, id1, season1 = select_player("player1")
        shots1 = load_shots(id1, season1)
        st.subheader(name1)
        show_statistics(shots1)
        show_shot_map(shots1)
    with col2:
        st.subheader("Player 2")
        name2, id2, season2 = select_player("player2")
        shots2 = load_shots(id2, season2)
        st.subheader(name2)
        show_statistics(shots2)
        show_shot_map(shots2)
