SETTING = "RLBot";
EXPERIMENTAL_FEATURES = false;
TWITCH_CHANNEL = "rlbotofficial";
FPS = 60;
// end of settings

LOGO_SRC = {
    WinterTide: "logo.png",
    RLBot: "rlbot_logo.png",
    Johnnyboi_i: "johnnyboi_i.png"
}[SETTING];

let vid = document.getElementById("Goal_Splash");
vid.pause();
vid.currentTime = 0;

game_stats = {
    last_total_goals: 0,
    mult: 0,

    blue_saves: 0,
    blue_shots: 0,
    blue_demos: 0,
    blue_names: [],
    blue_votes: 0.5,

    orange_saves: 0,
    orange_shots: 0,
    orange_demos: 0,
    orange_names: [],
    orange_votes: 0.5,

    is_done: false,
    started: false
};

loadRunner()

function loadRunner() {
    setInterval(function () {
        eel.get_game_tick_packet()().then(packet => {
            console.log("Loaded LoadRunner")
            blue_names = document.getElementById("Bot_Name_Blue");
            orange_names = document.getElementById("Bot_Name_Orange");

            if (packet.game_info.is_match_ended || packet.game_cars === 0) {

                for (let el of document.getElementsByClassName("hide-after-match")) {
                    el.style.display = "none"
                }
                blue_names.innerHTML = "Game ended";
                orange_names.innerHTML = "Game ended";
                game_stats.last_total_goals = 0;
                game_stats.blue_names = [];
                game_stats.orange_names = [];
                game_stats.blue_votes = 1;
                game_stats.orange_votes = 1;

            } else {
                game_stats.mult = 1;  // + (packet.game_info.time_elapsed / 300)
                game_stats.is_done = false;
                game_stats.started = true;

                for (let el of document.getElementsByClassName("hide-after-match")) {
                    if (el.style.display === "none") {
                        style = "flex";
                        if (el.classList.contains("set")) {
                            style = "initial"
                        }
                        el.style.display = style
                    }
                }

                blue_cars = [];
                orange_cars = [];

                new_blue_saves = 0;
                new_blue_shots = 0;
                new_blue_demos = 0;

                new_orange_saves = 0;
                new_orange_shots = 0;
                new_orange_demos = 0;

                goal_amount = 0;

                for (let el of packet.game_cars) {
                    goal_amount += el.score_info.goals;

                    if (el.name !== "") {
                        if (el.team === 0) {
                            bboost = el.boost;
                            bboostid = document.getElementById("Boost_Fill_Blue")
                            bboost = bboost/100;

                            bboostid.style.transform = "scaleY(" + bboost + ")";
                            // blue_cars.push(el);
                            // new_blue_shots += el.score_info.shots;
                            // new_blue_saves += el.score_info.saves;
                            // new_blue_demos += el.score_info.demolitions
                        } else {
                            orange_cars.push(el);
                            new_orange_shots += el.score_info.shots;
                            new_orange_saves += el.score_info.saves;
                            new_orange_demos += el.score_info.demolitions
                        }
                    }
                }

                // if (new_blue_demos > game_stats.blue_demos) {
                //     game_stats.blue_demos = new_blue_demos;
                //     blue_action("demo")
                // } else if (new_blue_shots > game_stats.blue_shots) {
                //     game_stats.blue_shots = new_blue_shots;
                //     blue_action("shot")
                // } else if (new_blue_saves > game_stats.blue_saves) {
                //     game_stats.blue_saves = new_blue_saves;
                //     blue_action("save")
                // }
                //
                // if (new_orange_demos > game_stats.orange_demos) {
                //     game_stats.orange_demos = new_orange_demos;
                //     orange_action("demo")
                // } else if (new_orange_shots > game_stats.orange_shots) {
                //     game_stats.orange_shots = new_orange_shots;
                //     orange_action("shot")
                // } else if (new_orange_saves > game_stats.orange_saves) {
                //     game_stats.orange_saves = new_orange_saves;
                //     orange_action("save")
                // }

                if (goal_amount > game_stats.last_total_goals) {
                    game_stats.last_total_goals = goal_amount;
                    setTimeout(do_goal_splash, 1080)
                    // setTimeout(do_goal_splash, 11100)
                }
                //
                // game_stats.blue_names = blue_cars.map(x => x.name);
                // game_stats.blue_names[blue_cars.length] = "blue";
                // game_stats.orange_names = orange_cars.map(x => x.name);
                // game_stats.orange_names[orange_cars.length] = "orange";
                //
                // if (blue_cars.length === 1) {
                //     blue_name = blue_cars[0].name
                // } else if (blue_cars.length === 2) {
                //     blue_name = blue_cars[0].name + " & " + blue_cars[1].name
                // } else {
                //     cars = blue_cars.map(x => x.name);
                //     blue_name = cars.slice(0, cars.length - 1).join(", ") + " & " + cars[cars.length - 1]
                // }
                //
                // blue_names.innerHTML = blue_name;
                //
                // if (orange_cars.length === 1) {
                //     orange_name = orange_cars[0].name
                // } else if (orange_cars.length === 2) {
                //     orange_name = orange_cars[0].name + " & " + orange_cars[1].name
                // } else {
                //     cars = orange_cars.map(x => x.name);
                //     orange_name = cars.slice(0, cars.length - 1).join(", ") + " & " + cars[cars.length - 1]
                // }

                // orange_names.innerHTML = orange_name
            }
        })
    // }, (1000))
    }, (1000 / FPS))
}

// function nameToTokens(name) {
//     return name.toLowerCase().replace("bot", "").split(" ")
// }
//
// function getTeamVotedFor(message) {
//     for (let word of message.toLowerCase().replace("bot", "").split(" ")) {
//         for (let player of game_stats.blue_names) {
//             for (let key of nameToTokens(player)) {
//                 if (key === word) {
//                     return "blue"
//                 }
//             }
//         }
//
//         for (let player of game_stats.orange_names) {
//             for (let key of nameToTokens(player)) {
//                 if (key === word) {
//                     return "orange"
//                 }
//             }
//         }
//     }
// }

// function setOrangeVotePercentage(votes, total) {
//     percentage = votes / total;
//     new_px_width = Math.round(311 * percentage);
//     new_px_dist = 147 + (311 - new_px_width);
//     el = document.getElementById("votes-orange");
//     el.style.width = new_px_width.toString() + "px";
//     el.style.right = new_px_dist.toString() + "px"
// }
//
// function setBlueVotePercentage(votes, total) {
//     percentage = votes / total;
//     new_px_width = Math.round(311 * percentage);
//     new_px_dist = 149 + (311 - new_px_width);
//     el = document.getElementById("votes-blue");
//     el.style.width = new_px_width.toString() + "px";
//     el.style.left = new_px_dist.toString() + "px"
// }
//
// function updateTeams() {
//     orange = game_stats.orange_votes;
//     blue = game_stats.blue_votes;
//     total = orange + blue;
//     setBlueVotePercentage(blue, total);
//     setOrangeVotePercentage(orange, total)
// }

function do_goal_splash() {
    vid = document.getElementById("Goal_Splash");

    vid.style.display = "block";
    vid.play();
    setTimeout(function () {
        vid.style.display = "none";
        vid.pause();
        vid.currentTime = 0
    }, 2000)
}

// function blue_action(action) {
//     src = "/imgs/" + action + ".png";
//     el = document.getElementById("blue-action");
//     el.src = src;
//     if (el.classList.contains("fade-out")) {
//         el.classList.remove("fade-out");
//         el.classList.add("fade-in")
//     }
//     setTimeout(function () {
//         el.classList.remove("fade-in");
//         el.classList.add("fade-out")
//     }, 2500)
// }

// function orange_action(action) {
//     src = "/imgs/" + action + ".png";
//     el = document.getElementById("orange-action");
//     el.src = src;
//     if (el.classList.contains("fade-out")) {
//         el.classList.remove("fade-out");
//         el.classList.add("fade-in")
//     }
//     setTimeout(function () {
//         el.classList.remove("fade-in");
//         el.classList.add("fade-out")
//     }, 2500)
// }

    // function get_most_votes() {
    //     if (game_stats.blue_votes === game_stats.orange_votes) {
    //         return null
    //     } else if (game_stats.blue_votes > game_stats.orange_votes) {
    //         return "Blue team"
    //     } else {
    //         return "Orange team"
    //     }
    // }
    //
    // stats = {
    //     "goals": {"name": "Most goals", "value": get_max("goals", packet.game_cars), "title": (res) => res.name},
    //     "points": {"name": "Most points", "value": get_max("points", packet.game_cars), "title": (res) => res.name},
    //     "assists": {"name": "Most assists", "value": get_max("assists", packet.game_cars), "title": (res) => res.name},
    //     "shots": {"name": "Most shots", "value": get_max("shots", packet.game_cars), "title": (res) => res.name},
    //     "demos": {
    //         "name": "Most demolitions",
    //         "value": get_max("demolitions", packet.game_cars),
    //         "title": (res) => res.name
    //     },
    //     "owns": {"name": "Most own goals", "value": get_max("own_goals", packet.game_cars), "title": (res) => res.name},
    //     "saves": {"name": "Most saves", "value": get_max("saves", packet.game_cars), "title": (res) => res.name},
    //     "hyped": {"name": "Most hyped", "value": get_most_votes(), "title": res => res},
    // };

    // items = [];
    // while (items.length < 3) {
    //     item = random_prop(stats);
    //     is_in = false;
    //     for (let item_in of items) {
    //         if (item_in.name === item.name) {
    //             is_in = true
    //         }
    //     }
    //
    //     if (!is_in && item.value != null) {
    //         items[items.length] = item
    //     }
    // }

    // console.log(stats);
    // console.log(items);

    // tags = items.map((it) => {
    //     return "<div class='stat-entry'><div class='stat-name'>" + it.name + "</div><div class='stat-value'>" + it.title(it.value) + "</div></div>"
    // });
    // end_div.innerHTML = tags.join("<br/>");
    //
    // for (let el of document.getElementsByClassName("endgame-appear")) {
    //     el.classList.remove("fade-out");
    //     el.classList.add("fade-in");
    //
    //     setTimeout(function () {
    //         el.classList.remove("fade-in");
    //         el.classList.add("fade-out")
    //     }, 10000)
    // }
// }
