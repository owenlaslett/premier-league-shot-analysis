# These are the libaries- code that someone else has written, which has been imported
import streamlit as st # Creates the interactive website- we are assigning streamlit as st to give it a shorter name
from understatapi import UnderstatClient # Downloads football statistics
from mplsoccer import VerticalPitch # Draws pitch
from matplotlib.lines import Line2D # Plots shots
import matplotlib.pyplot as plt # Creates goal and shot legend- we are assigning matplotlib a shorter name too (plt)

# Configure the dashboard
st.set_page_config( # Sets the browser tab title and page layout
    page_title="Premier League Analytics",
    layout="wide" # Uses the whole screen
)
st.markdown(""" 
<style>
.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True) # This code stops the content streching across entire monitor and reduces excessive space at the top

st.title("Premier League Shot Analysis") # Main heading
season_options = {
    "2026/27": "2026",   
    "2025/26": "2025", 
    "2024/25": "2024", 
    "2023/24": "2023", 
    "2022/23": "2022" 
}
selected_season = st.selectbox( # Creates a dropdown menu
    "Select a season:",
    list(season_options.keys()) # Displays the keys of the dictionary, which are the seasons
)

season = season_options[selected_season] # Associates the selected season with its corresponding value in the dictionary


# Download the player list
@st.cache_data(ttl=3600) # Decorator used, which tells Streamlit to remember the result for an hour, to reduce any unnecessary requests
def load_players(season): # Function defined
    with UnderstatClient() as understat: # Creates a client of communicating with Understat, and the with statement closes the client when finished with
        players = understat.league(
            league="EPL" # Selects Premier League
        ).get_player_data(season=season) #Season
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

# Create a player selection menu
players = load_players(season) # Calls load_players function we defined earlier

player_options = {
    player["player_name"]: player["id"] # Creates a dictionary
    for player in players
}

left_panel, right_panel = st.columns([1,1.3]) # Splits the avaliable spaces into columns, first gets 1/2.3, senond gets 1.3/2.3

with left_panel:
    selected_name = st.selectbox( # Creats a dropdown menu
    "Select a player:",
    sorted(player_options.keys()) # Sorted arranges the names alphabetically, and .keys() retrieves the players names from the dictionary
)

# Get the selected player's shots
player_id = player_options[selected_name] # Associates the ID with the player selected
shots = load_shots(player_id, season) # Calls load_shots to retrieve their shots, from the specific season that was chosen

# Calculate statistics
goals = [shot for shot in shots if shot["result"] == "Goal"] # This caluclates a list of goals, and checks to see if a shot outcome is == (equal) to a goal
total_xg = sum(float(shot["xG"]) for shot in shots) # shot["xG"] retrieves expected goal value of the shot, float () converts that number to a decimal, for loop goes through every shot, sum() adds them together
xg_per_shot = total_xg/len(shots) if shots else 0 # Calculates the average quality of players shots

# Display player statistics
with left_panel:
    st.subheader(selected_name) # Creates a heading with the selected players name

    stat1, stat2 = st.columns(2) # 2x2 stats on RHS
    stat3, stat4 = st.columns(2) # 2x2 stats on RHS

    stat1.metric("Total Shots", len(shots), border=True) # len counts how many items are in a collection
    stat2.metric("Goals", len(goals), border=True)
    stat3.metric("Expected Goals", f"{total_xg:.2f}", border=True) # :.2f rounds to 2 decimal places
    stat4.metric("xG per shot", f"{xg_per_shot:.3f}", border=True) # :.3f rounds to 3 decimal places



pitch = VerticalPitch( # Creates the vertical football pitch
    pitch_type="statsbomb",
    half=True, # Only display a half of the pitch
    pitch_color="#101820",
    line_color="white",
    line_zorder=2
)

fig, ax = pitch.draw(figsize=(5, 6)) # fig is overall figure, ax is area where pitch and shot markers are drawn
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
           markersize=10, label="Other shot")
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
with right_panel:
    st.subheader ("Player Shot Map")
    st.pyplot(fig) # Takes matplotlib figure and displays it inside Streamlit

# Close the Matplotlib figure to free memory
plt.close(fig)
