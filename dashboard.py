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
st.write("2026/27 Season") # Text 

# Download the player list
@st.cache_data(ttl=3600) # Decorator used, which tells Streamlit to remember the result for an hour, to reduce any unnecessary requests
def load_players(): # Function defined
    with UnderstatClient() as understat: # Creates a client of communicating with Understat, and the with statement closes the client when finished with
        players = understat.league(
            league="EPL" # Selects Premier League
        ).get_player_data(season="2026") #26/27 Season
    return players # Gives list of all players to the function 

# Download a selected player's shots
@st.cache_data(ttl=3600)
def load_shots(player_id): # Unique player identifier
    with UnderstatClient() as understat:
        all_shots = understat.player(
            player=player_id
        ).get_shot_data()

    return [
        shot for shot in all_shots # Returns when it meets a condtion, in a for loop
        if str(shot["season"]) == "2026"
    ]

# Create a player selection menu
players = load_players() # Calls load_players function we defined earlier

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
shots = load_shots(player_id) # Calls load_shots to retrieve their shots

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
    line_color="white"
)

fig, ax = pitch.draw(figsize=(5, 6)) # fig is overall figure, ax is area where pitch and shot markers are drawn
fig.patch.set_facecolor("#101820")

# Separate goals from other shots
goals = [shot for shot in shots if shot["result"] == "Goal"]
misses = [shot for shot in shots if shot["result"] != "Goal"]

# Plot other shots
pitch.scatter( # plots circles on the pitch
    [float(shot["X"]) * 120 for shot in misses], # Multiplying by 120 allows convertion from Understat shot coordinates to StatsBomb pitch representation
    [80 - float(shot["Y"]) * 80 for shot in misses], # Subtraction needed as the shot map was initially mirrored
    s=[80 + float(shot["xG"]) * 650 for shot in misses], # s controls the area of each circle, with s = 80+ 650(xG)
    color="white",
    edgecolors="black",
    ax=ax
)

# Plot goals
pitch.scatter(
    [float(shot["X"]) * 120 for shot in goals],
    [80 - float(shot["Y"]) * 80 for shot in goals],
    s=[80 + float(shot["xG"]) * 650 for shot in goals],
    color="red",
    edgecolors="white",
    ax=ax
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

ax.legend(
    handles=legend_elements,
    loc="lower left", # Places legend in top corner
    facecolor="#101820",
    labelcolor="white",
    edgecolor="white"
)

# Display the pitch inside Streamlit
with right_panel:
    st.subheader ("Player Shot Map")
    st.pyplot(fig) # Takes matplotlib figure and displays it inside Streamlit

# Close the Matplotlib figure to free memory
plt.close(fig)
