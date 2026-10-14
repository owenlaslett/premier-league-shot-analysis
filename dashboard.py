
# These are the libraries - code that someone else has written, which has been imported
import streamlit as st # Creates the interactive website
from understatapi import UnderstatClient # Downloads football statistics
from mplsoccer import VerticalPitch # Draws pitch
from matplotlib.lines import Line2D # Plots shots
import matplotlib.pyplot as plt # Creates goal and shot legend
import html

# Configure the dashboard
st.set_page_config(
    page_title="Premier League Analytics",
    layout="wide"
)

st.markdown("""
<style>

/* Main dashboard background */
.stApp {
    background-color: #F0F4F8;
}

/* Match the header to the background */
[data-testid="stHeader"],
[data-testid="stAppHeader"],
.stApp > header {
    background-color: #F0F4F8 !important;
}

/* White statistics boxes */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #D5DCE5 !important;
    border-radius: 8px !important;
    padding: 8px !important;
}

/* Reduce number size so values fit */
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
}

/* Make metric labels more compact */
[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
}

/* Make dropdown boxes white */
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #D5DCE5 !important;
    border-radius: 8px !important;
    color: #172033 !important;
}

/* Keep dropdown text dark */
div[data-baseweb="select"] span {
    color: #172033 !important;
}

/* Blue outline when selecting */
div[data-baseweb="select"]:focus-within > div {
    border-color: #6B93BC !important;
    box-shadow: 0 0 0 1px #6B93BC !important;
}

/* Dashboard width and spacing */
.block-container {
    max-width: 1400px;
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* White dropdown backgrounds */
.stSelectbox div[data-baseweb="select"] > div:first-child {
    background-color: #FFFFFF !important;
    border: 1px solid #D5DCE5 !important;
    border-radius: 8px !important;
}

/* Dark dropdown text */
.stSelectbox div[data-baseweb="select"] {
    color: #172033 !important;
}

</style>
""", unsafe_allow_html=True)

st.title("Premier League Shot Analysis")

season_options = {
    "2026/27": "2026",
    "2025/26": "2025",
    "2024/25": "2024",
    "2023/24": "2023",
    "2022/23": "2022"
}

# Download the player list
@st.cache_data(ttl=3600)
def load_players(season):
    with UnderstatClient() as understat:
        players = understat.league(
            league="EPL"
        ).get_player_data(season=season)
    return players

# Download a selected player's shots
@st.cache_data(ttl=3600)
def load_shots(player_id, season):
    with UnderstatClient() as understat:
        all_shots = understat.player(
            player=player_id
        ).get_shot_data()
    return [
        shot for shot in all_shots
        if str(shot["season"]) == season
    ]

# Fix player names containing apostrophes or HTML characters
def readable_name(name):
    name = str(name)

    # Some names are encoded more than once
    for _ in range(3):
        corrected = html.unescape(name)
        if corrected == name:
            break
        name = corrected
    return name

# Select season, club and player on one horizontal row
def select_player(key_prefix):
    season_col, club_col, player_col = st.columns(
        [1, 1, 1.3],
        gap="small"
    )

    # Select the season
    with season_col:
        selected_season = st.selectbox(
            "Season:",
            list(season_options.keys()),
            key=f"{key_prefix}_season"
        )
    season = season_options[selected_season]

    # Download players from the selected season
    players = load_players(season)

    # Find all clubs in that season
    clubs = sorted({
        readable_name(club.strip())
        for player in players
        for club in str(
            player.get("team_title") or ""
        ).split(",")
        if club.strip()
    })

    # Select the club
    with club_col:
        selected_club = st.selectbox(
            "Club:",
            ["All Clubs"] + clubs,
            key=f"{key_prefix}_club"
        )

    # Filter players by their selected club
    filtered_players = [
        player for player in players
        if selected_club == "All Clubs"
        or selected_club in [
            readable_name(club.strip())
            for club in str(
                player.get("team_title") or ""
            ).split(",")
        ]
    ]

    player_options = {
        readable_name(player["player_name"]): player["id"]
        for player in filtered_players
    }

    # Select the player
    with player_col:
        selected_name = st.selectbox(
            "Player:",
            sorted(player_options.keys()),
            key=f"{key_prefix}_player"
        )

    return selected_name, player_options[selected_name], season

# Calculate and display shooting statistics
def show_statistics(shots):
    goals = [
        shot for shot in shots
        if shot["result"] == "Goal"
    ]
    total_xg = sum(float(shot["xG"]) for shot in shots)
    xg_per_shot = (
        total_xg / len(shots)
        if shots else 0
    )

    stat1, stat2, stat3, stat4 = st.columns(4)
    stat1.metric("Shots", len(shots), border=True)
    stat2.metric("Goals", len(goals), border=True)
    stat3.metric(
        "xG",
        f"{total_xg:.2f}",
        border=True
    )
    stat4.metric(
        "xG/Shot",
        f"{xg_per_shot:.2f}",
        border=True
    )

# Create a shot map for the selected player
def show_shot_map(shots):
    pitch = VerticalPitch(
        pitch_type="statsbomb",
        half=True,
        pitch_color="#101820",
        line_color="white",
        line_zorder=2
    )

    fig, ax = pitch.draw(figsize=(4, 5))
    fig.patch.set_facecolor("#101820")

    # Convert Understat coordinates to StatsBomb coordinates
    shot_x = [float(shot["X"]) * 120 for shot in shots]
    shot_y = [80 - float(shot["Y"]) * 80 for shot in shots]

    # Only create a heatmap if there are enough shots
    if len(shots) >= 5 and len(set(shot_x)) > 1 and len(set(shot_y)) > 1:
        pitch.kdeplot(
            shot_x,
            shot_y,
            ax=ax,
            fill=True,
            levels=20,
            cmap="magma",
            alpha=0.6,
            bw_adjust=0.9,
            thresh=0.15,
            cut=2,
            zorder=1
        )

    # Separate goals from other shots
    goals = [shot for shot in shots if shot["result"] == "Goal"]
    misses = [shot for shot in shots if shot["result"] != "Goal"]

    # Plot other shots
    pitch.scatter(
        [float(shot["X"]) * 120 for shot in misses],
        [80 - float(shot["Y"]) * 80 for shot in misses],
        s=[25 + float(shot["xG"]) * 100 for shot in misses],
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

    # Add goal and miss legend
    legend_elements = [
        Line2D(
            [0], [0],
            marker="o",
            color="none",
            markerfacecolor="red",
            markeredgecolor="white",
            markersize=10,
            label="Goal"
        ),
        Line2D(
            [0], [0],
            marker="o",
            color="none",
            markerfacecolor="white",
            markeredgecolor="black",
            markersize=10,
            label="Miss"
        )
    ]

    goal_legend = ax.legend(
        handles=legend_elements,
        loc="lower left",
        facecolor="#101820",
        labelcolor="white",
        edgecolor="white",
        fontsize=11,
        prop={"family": "DejaVu Sans", "size": 11},
        handlelength=0.8,
        handletextpad=0.3
    )

    # Keep first legend visible
    ax.add_artist(goal_legend)

    # Add xG shot size legend
    xg_values = [0.05, 0.30, 0.70]

    xg_handles = [
        Line2D(
            [0], [0],
            marker="o",
            linestyle="None",
            markerfacecolor="white",
            markeredgecolor="black",
            markersize=(25 + xg * 100) ** 0.5,
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
