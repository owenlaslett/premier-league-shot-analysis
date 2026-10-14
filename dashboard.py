# These are the libaries- code that someone else has written, which has been imported

import streamlit as st # Creates the interactive website- we are assigning streamlit as st to give it a shorter name

from understatapi import UnderstatClient # Downloads football statistics

from mplsoccer import VerticalPitch # Draws pitch

from matplotlib.lines import Line2D # Plots shots

import matplotlib.pyplot as plt # Creates goal and shot legend- we are assigning matplotlib a shorter name too (plt)

import html

# Configure the dashboard

st.set_page_config( # Sets the browser tab title and page layout

    page_title="Premier League Analytics",

    layout="wide" # Uses the whole screen

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



 # This code stops the content streching across entire monitor and reduces excessive space at the top

st.title("Premier League Shot Analysis") # Main heading

season_options = {

    "2026/27": "2026",   

    "2025/26": "2025", 

    "2024/25": "2024", 

    "2023/24": "2023", 

    "2022/23": "2022" 

}





# Download the player list

@st.cache_data(ttl=3600) # Decorator used, which tells Streamlit to remember the result for an hour, to reduce any unnecessary requests

def load_players(season): # Function defined

    with UnderstatClient() as understat: # Creates a client of communicating with Understat, and the with statement closes the client when finished with

        players = understat.league(

            league="EPL" # Selects Premier League

        ).get_player_data(season=season) #26/27 Season

    return players # Gives list of all players to the function 

# Download a selected player's shots

@st.cache_data(ttl=3600)

def load_shots(player_id, season): # Unique player identifier

    with UnderstatClient() as understat:

        all_shots = understat.player(

            player=player_id

        ).get_shot_data()

    return [

        shot for shot in all_shots # Returns when it meets a condtion, in a for loop

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

def show_shot_map(shots):

    pitch = VerticalPitch( # Creates the vertical football pitch

        pitch_type="statsbomb",

        half=True, # Only display a half of the pitch

        pitch_color="#101820",

        line_color="white",

        line_zorder=2

    )

    fig, ax = pitch.draw(figsize=(4, 5)) # fig is overall figure, ax is area where pitch and shot markers are drawn

    fig.patch.set_facecolor("#101820")

    # Create a shot-density heatmap

    # Convert Understat coordinates to StatsBomb coordinates

    shot_x = [float(shot["X"]) * 120 for shot in shots]

    shot_y = [80 - float(shot["Y"]) * 80 for shot in shots]

    # Only create a heatmap if there are enough shots

    if len(shots) >= 5 and len(set(shot_x)) > 1 and len(set(shot_y)) > 1: # skips heatmap of players with very few shots

        pitch.kdeplot(

            shot_x, # gets the position of every shot

            shot_y,

            ax=ax,

            fill=True, # full heat map

            levels=20, # 40 density colours

            cmap = "magma", # Dark purple, red and yellow palette

            alpha=0.6, # Slightly transparent 

            bw_adjust=0.9, # controls how smoothly shot locations are grouped

            thresh=0.15, # Hide low density areas

            cut=2,

            zorder=1 # Position heat maps behind pitch markings and shot circles

        )

    # Separate goals from other shots

    goals = [shot for shot in shots if shot["result"] == "Goal"]

    misses = [shot for shot in shots if shot["result"] != "Goal"]

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

