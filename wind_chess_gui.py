import random
import time
import os
import json
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from enum import Enum
from typing import List, Tuple, Optional, Dict
from datetime import datetime
import threading

class WindDirection(Enum):
    HORIZONTAL = "水平风"
    VERTICAL = "垂直风"
    DIAGONAL = "旋风"

class Player(Enum):
    A = "●"
    B = "○"

class GameMode(Enum):
    TUTORIAL = "新手介绍"
    PVP = "玩家对战"
    PVE = "美少女对战"
    CHAT = "与风子聊天"

class BoardSize(Enum):
    SMALL = (5, 5, 4, "5×5")      # 5x5, 4个棋子
    MEDIUM = (9, 9, 6, "9×9")     # 9x9, 6个棋子
    LARGE = (16, 16, 8, "16×16")  # 16x16, 8个棋子

class AchievementManager:
    """成就管理器，记录玩家进度和特殊剧情触发"""

    def __init__(self, save_file="wind_chess_save.json"):
        self.save_file = save_file
        self.data = self._load_data()

    def _load_data(self):
        """加载保存数据"""
        default_data = {
            "achievements": {
                "small_wins": 0,  # 5x5胜利次数
                "medium_wins": 0, # 9x9胜利次数
                "large_wins": 0,  # 16x16胜利次数
                "small_losses": 0,  # 5x5失败次数
                "medium_losses": 0, # 9x9失败次数
                "large_losses": 0,  # 16x16失败次数
                "total_games": 0,   # 总游戏次数
                "total_wins": 0,    # 总胜利次数
                "total_losses": 0,  # 总失败次数
                "favorability": 0,  # 好感度
                "special_events_triggered": {
                    "all_win_special": False,
                    "all_lose_special": False
                },
                "season_events": {
                    "spring": False,
                    "summer": False,
                    "autumn": False,
                    "winter": False
                },
                "games_since_last_event": 0
            },
            "settings": {
                "dialogue_display_time": 4,  # 默认4秒
                "music_enabled": True,
                "sound_effects_enabled": True
            },
            "statistics": {
                "first_play_date": datetime.now().strftime("%Y-%m-%d"),
                "last_play_date": datetime.now().strftime("%Y-%m-%d"),
                "total_play_time": 0
            }
        }

        try:
            if os.path.exists(self.save_file):
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    for key, value in default_data.items():
                        if key not in loaded_data:
                            loaded_data[key] = value
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                if sub_key not in loaded_data[key]:
                                    loaded_data[key][sub_key] = sub_value
                    return loaded_data
        except:
            pass

        return default_data

    def save(self):
        """保存数据"""
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def record_game_result(self, board_size: BoardSize, player_won: bool):
        """记录游戏结果"""
        size_key = {
            BoardSize.SMALL: "small",
            BoardSize.MEDIUM: "medium",
            BoardSize.LARGE: "large"
        }[board_size]

        if player_won:
            self.data["achievements"][f"{size_key}_wins"] += 1
            self.data["achievements"]["total_wins"] += 1
        else:
            self.data["achievements"][f"{size_key}_losses"] += 1
            self.data["achievements"]["total_losses"] += 1

        self.data["achievements"]["total_games"] += 1
        self.data["achievements"]["games_since_last_event"] += 1
        self.data["statistics"]["last_play_date"] = datetime.now().strftime("%Y-%m-%d")
        self.save()

    def add_favorability(self, amount: int):
        """增加好感度"""
        self.data["achievements"]["favorability"] += amount
        if self.data["achievements"]["favorability"] < 0:
            self.data["achievements"]["favorability"] = 0
        self.save()

    def get_favorability(self) -> int:
        """获取当前好感度"""
        return self.data["achievements"]["favorability"]

    def check_special_event_conditions(self):
        """检查特殊剧情触发条件"""
        achievements = self.data["achievements"]
        favorability = self.get_favorability()

        # 胜利结局需要好感度>=30
        all_win_condition = (
            achievements["small_wins"] >= 2 and
            achievements["medium_wins"] >= 2 and
            achievements["large_wins"] >= 2 and
            favorability >= 30 and
            not achievements["special_events_triggered"]["all_win_special"]
        )

        # 失败结局需要好感度>=50
        all_lose_condition = (
            achievements["small_losses"] >= 2 and
            achievements["medium_losses"] >= 2 and
            achievements["large_losses"] >= 2 and
            favorability >= 50 and
            not achievements["special_events_triggered"]["all_lose_special"]
        )

        return all_win_condition, all_lose_condition

    def check_season_event_condition(self) -> bool:
        """检查是否触发季节事件"""
        return self.data["achievements"]["games_since_last_event"] >= 5

    def trigger_special_event(self, event_type: str):
        """触发特殊事件"""
        if event_type == "all_win":
            self.data["achievements"]["special_events_triggered"]["all_win_special"] = True
        elif event_type == "all_lose":
            self.data["achievements"]["special_events_triggered"]["all_lose_special"] = True
        self.save()

    def trigger_season_event(self, season: str):
        """触发季节事件"""
        self.data["achievements"]["season_events"][season] = True
        self.data["achievements"]["games_since_last_event"] = 0
        self.save()

    def get_special_events_count(self):
        """获取已触发的特殊事件数量"""
        triggered = self.data["achievements"]["special_events_triggered"]
        return sum(1 for event in triggered.values() if event)

    def update_setting(self, key: str, value):
        """更新设置"""
        if key in self.data["settings"]:
            self.data["settings"][key] = value
            self.save()

    def get_setting(self, key: str):
        """获取设置值"""
        return self.data["settings"].get(key)

class ACGNBeautyGirl:
    """ACGN风格的美少女对手角色"""

    def __init__(self, name: str = "风子"):
        self.name = name
        self.personality = "傲娇勇敢"
        self.relationship_level = 0
        self.win_streak = 0
        self.lose_streak = 0
        self.dialogue_sets = self._create_dialogue_sets()

    def _create_dialogue_sets(self) -> Dict[str, List[str]]:
        """创建丰富的ACGN风格对话库"""
        return {
            "game_start": [
                "哼哼，今天就让前辈见识一下我的实力！",
                "风之棋可是我最拿手的游戏呢！",
                "虽然有点紧张，但我不会输的！",
                "前辈，让我们来一场不留遗憾的对决吧！"
            ],
            "my_turn": [
                "看我的！风之刃·斩！",
                "这一招可是我的得意技！",
                "风啊，回应我的呼唤吧！",
                "前辈，接招！"
            ],
            "good_ai_move": [
                "嘻嘻，这步棋不错吧！",
                "这就是我的战术风格！",
                "前辈被我的智慧折服了吗？",
                "哼哼，我可是有认真研究过的！"
            ],
            "bad_ai_move": [
                "哎呀...这步好像不太妙...",
                "呜...大意了...",
                "刚才那个不算！我重新想一下！",
                "前、前辈不要笑我啦！"
            ],
            "player_good_move": [
                "哇！前辈这步棋好厉害！",
                "不愧是前辈，果然有两下子！",
                "看来我得更加认真才行！",
                "前辈进步了呢！不过我不会认输的！"
            ],
            "player_bad_move": [
                "诶？前辈这步棋是让着我吗？",
                "嘻嘻，前辈大意了呢！",
                "这就是我的机会！",
                "前辈的战术被我看穿了哦！"
            ],
            "winning_streak": [
                "胜利的滋味真不错呢！再来！",
                "哼哼，前辈已经跟不上我的节奏了吗？",
                "风之棋果然是我的主场！",
                "前辈，认输也是可以的哦！"
            ],
            "losing_streak": [
                "呜...怎么会这样...",
                "前辈太强了...但是我不会放弃的！",
                "明明就差一点点了...",
                "风啊...请再给我一点力量..."
            ],
            "victory": [
                "耶！我赢了！前辈看到了吗！",
                "胜利！这就是我的真正实力！",
                "哼哼，知道我的厉害了吧前辈！",
                "赢啦！前辈要请我吃冰淇淋哦！"
            ],
            "defeat": [
                "呜哇...输了...前辈好过分...",
                "明明就差一点点的...前辈欺负人...",
                "今天的状态不太好...下次一定会赢的！",
                "前辈太强了...让我再挑战一次嘛！"
            ],
            "critical_move": [
                "这一招！赌上我所有的荣耀！",
                "必杀！风神之舞！",
                "接招吧！这就是我的觉悟！",
                "前辈，这就是我的全力一击！"
            ],
            "wind_change": [
                "风向变了呢...我的机会来了！",
                "新的风向，新的战术！",
                "风在指引我走向胜利！",
                "前辈，跟上风的节奏吧！"
            ],
            "almost_win": [
                "还差一点！还差一点我就要赢了！",
                "胜利就在眼前！前辈准备好了吗！",
                "这一局我拿下了！",
                "看我的最后一击！"
            ],
            "almost_lose": [
                "呜呜...难道又要输了吗...",
                "前辈不要得意，我还有机会！",
                "我不会这么轻易认输的！",
                "逆转的机会...一定有的..."
            ],
            "encouragement": [
                "前辈，让我们都发挥出全力吧！",
                "不管输赢，这都是宝贵的经历呢！",
                "能和前辈对战，我很开心！",
                "让我们创造美好的回忆吧！"
            ],
            "special_actions": [
                "前辈看好了！风之秘技！",
                "这是我从漫画里学到的招式！",
                "赌上我美少女棋士的尊严！",
                "风子酱，全力全开！"
            ],
            "daily_greeting": [
                "前辈，今天也请多指教！",
                "啊，前辈来了！我等你好久了！",
                "前辈今天看起来精神不错呢！",
                "准备好开始今天的对局了吗，前辈？"
            ],
            "after_game": [
                "今天和前辈下棋很开心！",
                "前辈又进步了呢！",
                "下次我一定会赢回来的！",
                "和前辈下棋的时间总是过得很快呢～"
            ]
        }

    def get_dialogue(self, situation: str) -> str:
        """获取情境对话"""
        if situation not in self.dialogue_sets:
            return ""

        dialogues = self.dialogue_sets[situation]
        if not dialogues:
            return ""

        if self.win_streak >= 3:
            dialogues = [d.replace("前辈", "手下败将") for d in dialogues]
        elif self.lose_streak >= 3:
            dialogues = [d + " (泪眼汪汪)" for d in dialogues]

        if self.relationship_level > 5:
            dialogues = [d.replace("前辈", "亲爱的对手") for d in dialogues]

        return random.choice(dialogues)

    def update_relationship(self, player_won: bool):
        """更新关系等级"""
        if player_won:
            self.lose_streak += 1
            self.win_streak = 0
            self.relationship_level += 1
        else:
            self.win_streak += 1
            self.lose_streak = 0
            self.relationship_level += 0.5

    def get_emotional_state(self) -> str:
        """获取当前情绪状态"""
        if self.win_streak >= 3:
            return "得意洋洋"
        elif self.lose_streak >= 3:
            return "垂头丧气"
        elif self.relationship_level > 5:
            return "亲密友好"
        else:
            return "斗志昂扬"

class WindGameAI:
    """智能AI对手"""

    def __init__(self, difficulty: str = "medium"):
        self.difficulty = difficulty

    def evaluate_board(self, board, board_size, player, wind_direction) -> float:
        """评估棋盘状态"""
        score = 0
        center = board_size // 2

        player_pieces = sum(1 for row in board for cell in row if cell == player)
        opponent_pieces = sum(1 for row in board for cell in row if cell is not None and cell != player)
        score += (player_pieces - opponent_pieces) * 10

        if board[center][center] == player:
            score += 30

        score += self._evaluate_lines(board, board_size, player) * 15
        score += self._evaluate_mobility(board, board_size, player, wind_direction) * 5

        return score

    def _evaluate_lines(self, board, board_size, player) -> int:
        """评估连线潜力"""
        lines = 0
        center = board_size // 2

        for y in range(board_size):
            for x in range(board_size):
                if board[y][x] == player:
                    distance_to_center = abs(x - center) + abs(y - center)
                    lines += (board_size - distance_to_center) * 2

        return lines

    def _evaluate_mobility(self, board, board_size, player, wind_direction) -> int:
        """评估移动灵活性"""
        mobility = 0
        center = board_size // 2

        for y in range(board_size):
            for x in range(board_size):
                if board[y][x] == player:
                    if (x, y) == (center, center):
                        mobility += 8
                    elif wind_direction == WindDirection.HORIZONTAL:
                        mobility += 2
                    elif wind_direction == WindDirection.VERTICAL:
                        mobility += 2
                    elif wind_direction == WindDirection.DIAGONAL:
                        mobility += 4

        return mobility

    def find_best_move(self, game_state) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """寻找最佳移动"""
        board = game_state["board"]
        board_size = game_state["board_size"]
        player = game_state["current_player"]
        wind_direction = game_state["wind_direction"]

        best_score = -float('inf')
        best_move = None

        all_moves = []
        for y in range(board_size):
            for x in range(board_size):
                if board[y][x] == player:
                    from_pos = (x, y)
                    valid_moves = self._get_valid_moves_simulation(board, board_size, from_pos, wind_direction)
                    for to_pos in valid_moves:
                        all_moves.append((from_pos, to_pos))

        if not all_moves:
            return None

        if self.difficulty == "easy":
            scored_moves = []
            for move in all_moves:
                from_pos, to_pos = move
                temp_board = [row[:] for row in board]
                temp_board[to_pos[1]][to_pos[0]] = player
                temp_board[from_pos[1]][from_pos[0]] = None

                score = self.evaluate_board(temp_board, board_size, player, wind_direction)
                scored_moves.append((score, move))

            scored_moves.sort(key=lambda x: x[0], reverse=True)
            if len(scored_moves) > 3:
                return scored_moves[random.randint(0, 2)][1]
            else:
                return scored_moves[0][1]
        else:
            for move in all_moves:
                from_pos, to_pos = move
                temp_board = [row[:] for row in board]
                temp_board[to_pos[1]][to_pos[0]] = player
                temp_board[from_pos[1]][from_pos[0]] = None

                score = self.evaluate_board(temp_board, board_size, player, wind_direction)

                opponent = Player.B if player == Player.A else Player.A
                opponent_score = self.evaluate_board(temp_board, board_size, opponent, wind_direction)

                final_score = score - opponent_score * 0.5

                if final_score > best_score:
                    best_score = final_score
                    best_move = move

        return best_move

    def _get_valid_moves_simulation(self, board, board_size, piece_pos, wind_direction):
        """模拟获取合法移动"""
        x, y = piece_pos
        center = board_size // 2
        valid_moves = []

        if (x, y) == (center, center):
            directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        elif wind_direction == WindDirection.HORIZONTAL:
            directions = [(-1,0), (1,0)]
        elif wind_direction == WindDirection.VERTICAL:
            directions = [(0,-1), (0,1)]
        elif wind_direction == WindDirection.DIAGONAL:
            directions = [(-1,-1), (-1,1), (1,-1), (1,1)]

        for dx, dy in directions:
            step = 1
            while True:
                nx, ny = x + dx*step, y + dy*step
                if not (0 <= nx < board_size and 0 <= ny < board_size):
                    break
                if board[ny][nx] is not None:
                    break
                valid_moves.append((nx, ny))
                step += 1

        return valid_moves

class GameTips:
    """游戏提示管理器"""

    def __init__(self):
        self.tips = self._create_tips()

    def _create_tips(self):
        """创建提示列表"""
        return [
            "提示：每次新手教程，风子说的话可能不一样哦～多玩几次教程会发现新内容！",
            "人物设定：风子是个傲娇但勇敢的美少女棋士，输了会撒娇，赢了会得意～",
            "游戏技巧：控制风眼是关键！风眼上的棋子可以无视风向移动。",
            "游戏技巧：注意风向变化，提前规划棋子位置。",
            "游戏技巧：连线时，底线上不能有超过1个棋子！",
            "人物设定：风子喜欢冰淇淋，赢了会要你请客哦！",
            "游戏技巧：大棋盘（9×9或16×16）需要更长远的战略规划。",
            "人物设定：风子的情绪会随胜负变化，连胜时会更得意～",
            "游戏技巧：阻挡对手的连线比创造自己的连线更重要！",
            "人物设定：风子有ACGN风格台词库，每次对话都可能有新内容！",
            "游戏技巧：利用棋子的长距离移动能力快速调整阵型。",
            "游戏技巧：记住，棋子不能跳过其他棋子。",
            "特殊剧情：在所有棋盘上都战胜AI超过两次会触发特殊剧情！",
            "特殊剧情：在所有棋盘上都输给AI超过两次也会触发特殊剧情！",
            "好感度系统：和风子聊天可以增加好感度，好感度影响特殊结局触发！",
            "季节事件：每隔5局游戏有概率触发特殊季节事件！",
            "小提示：可以在设置中调整风子对话的显示时间。"
        ]

    def get_random_tip(self):
        """获取随机提示"""
        return random.choice(self.tips)

class ChatSystem:
    """聊天系统"""

    def __init__(self, achievement_manager: AchievementManager):
        self.achievement_manager = achievement_manager
        self.topics = self._create_topics()
        self.daily_topics = self._create_daily_topics()

    def _create_topics(self):
        """创建聊天话题"""
        return {
            "chess": {
                "question": "前辈，你觉得风之棋最有趣的地方是什么？",
                "responses": [
                    ("风向的变化让游戏充满变数", 5, "嗯嗯！我也是这么觉得的！风向变化让游戏更有挑战性！"),
                    ("控制风眼的感觉很爽", 3, "嘻嘻，风眼确实很重要呢！前辈很有眼光～"),
                    ("没什么意思，就是普通的棋类游戏", -5, "呜...前辈这么说好伤人...风之棋明明很有趣的..."),
                    ("和你对战很开心", 10, "诶？！前、前辈突然说什么呢！我、我也很开心啦！")
                ]
            },
            "hobby": {
                "question": "前辈平时有什么兴趣爱好吗？",
                "responses": [
                    ("下棋，特别是和你下棋", 8, "前辈真是的！不过...我也喜欢和前辈下棋呢～"),
                    ("看书，特别是棋谱", 4, "诶～前辈好认真！我也要看更多的棋谱才行！"),
                    ("没什么特别的爱好", 0, "这样啊...前辈的生活有点单调呢..."),
                    ("玩游戏，各种类型的游戏", 3, "哦！那前辈一定很擅长策略游戏吧！")
                ]
            },
            "food": {
                "question": "前辈喜欢吃什么甜点？",
                "responses": [
                    ("冰淇淋，特别是香草味的", 7, "哇！我也是！前辈我们口味好像！下次一起去吃吧！"),
                    ("蛋糕，特别是草莓蛋糕", 5, "草莓蛋糕很好吃呢！甜甜的，软软的～"),
                    ("不喜欢甜食", -3, "诶？！怎么可以不喜欢甜食！甜食是世界上最棒的东西！"),
                    ("布丁，滑滑嫩嫩的", 6, "布丁！我也喜欢！特别是焦糖布丁！")
                ]
            },
            "future": {
                "question": "前辈将来想成为什么样的人？",
                "responses": [
                    ("职业棋手，和你一起参加比赛", 10, "前、前辈！我们一起努力！我一定会跟上你的！"),
                    ("普通的上班族，安稳的生活", 2, "这样啊...不过能安稳地生活也不错呢..."),
                    ("还没想好，走一步看一步", 0, "这样啊...不过前辈这么厉害，一定没问题的！"),
                    ("想一直和你下棋", 12, "呜...前辈今天怎么这么会说话...我好开心...")
                ]
            },
            "memory": {
                "question": "前辈还记得我们第一次下棋的时候吗？",
                "responses": [
                    ("记得，你紧张得手都在抖", 6, "啊啊！前辈不要说出来！那时候我确实很紧张嘛..."),
                    ("有点记不清了，我们下了很多次了", -2, "呜...前辈居然不记得了...我好难过..."),
                    ("记得，你赢了我还说'承让了前辈'", 8, "啊！那一次！前辈还记得这么清楚！"),
                    ("每次和你下棋都很开心，所以都记得", 15, "前、前辈！今天怎么总是说这种话！我都害羞了！")
                ]
            }
        }

    def _create_daily_topics(self):
        """创建日常话题"""
        return [
            "今天天气真好呢，前辈。",
            "前辈吃过午饭了吗？",
            "最近看到一本很有趣的棋谱，前辈要看吗？",
            "前辈今天看起来精神不错呢！",
            "啊，前辈的头发有点乱了，我帮你整理一下吧。",
            "前辈喜欢什么样的音乐？",
            "我最近在学做蛋糕，前辈要尝尝看吗？",
            "前辈，你觉得我今天的发饰好看吗？",
            "啊，前辈的袖口有点脏了，我帮你拍掉。",
            "前辈，我们明天也一起下棋吧！"
        ]

class SeasonEventManager:
    """季节事件管理器"""

    def __init__(self, achievement_manager: AchievementManager):
        self.achievement_manager = achievement_manager
        self.events = self._create_events()

    def _create_events(self):
        """创建季节事件"""
        return {
            "spring": {
                "title": "🌸 春日赏樱 🌸",
                "description": "春天到了，樱花盛开，风子邀请你一起去赏樱。",
                "scenes": [
                    "微风拂过，粉色的花瓣如雪般飘落。",
                    "风子穿着淡粉色的和服，在樱花树下向你招手。",
                    "她递给你一个樱花饼，脸上带着温柔的笑容。",
                    "阳光透过樱花洒在地上，形成斑驳的光影。",
                    "风子轻声说：'前辈，明年春天也一起来看樱花吧。'"
                ],
                "favorability_gain": 15
            },
            "summer": {
                "title": "🎆 夏日祭典 🎆",
                "description": "夏日祭典开始了，风子拉着你去逛庙会。",
                "scenes": [
                    "祭典上灯火通明，各种小吃摊和游戏摊排成一列。",
                    "风子穿着浴衣，手里拿着苹果糖，眼睛闪闪发亮。",
                    "你们一起玩了捞金鱼，虽然一条也没捞到。",
                    "烟花在夜空中绽放，照亮了风子开心的脸庞。",
                    "风子说：'和前辈一起的夏天，最开心了！'"
                ],
                "favorability_gain": 20
            },
            "autumn": {
                "title": "🍁 秋季露营 🍁",
                "description": "秋高气爽，风子提议一起去露营。",
                "scenes": [
                    "枫叶染红了山野，你们在湖边搭起了帐篷。",
                    "风子笨手笨脚地生火，脸上沾了炭灰。",
                    "你们一起烤棉花糖，看星星在夜空中闪烁。",
                    "篝火噼啪作响，风子靠在你的肩膀上睡着了。",
                    "清晨的湖面倒映着朝霞，风子轻声说：'谢谢前辈陪我。'"
                ],
                "favorability_gain": 18
            },
            "winter": {
                "title": "⛷️ 冬季滑雪 ⛷️",
                "description": "冬天到了，风子约你去滑雪。",
                "scenes": [
                    "雪山在阳光下闪闪发光，你们穿着滑雪服准备出发。",
                    "风子刚开始总是摔倒，但很快就掌握了技巧。",
                    "你们从山顶滑下，风在耳边呼啸。",
                    "滑完雪后，你们在木屋里喝着热可可。",
                    "风子的脸红红的，不知道是冻的还是害羞：'和前辈一起，冬天也不冷呢。'"
                ],
                "favorability_gain": 12
            }
        }

    def check_and_trigger_event(self):
        """检查并触发季节事件"""
        if not self.achievement_manager.check_season_event_condition():
            return None

        # 随机选择一个季节事件
        available_seasons = [season for season in self.events.keys()
                           if not self.achievement_manager.data["achievements"]["season_events"][season]]

        if not available_seasons:
            # 所有季节事件都触发过了，重置
            for season in self.achievement_manager.data["achievements"]["season_events"]:
                self.achievement_manager.data["achievements"]["season_events"][season] = False
            available_seasons = list(self.events.keys())

        selected_season = random.choice(available_seasons)
        event = self.events[selected_season]

        # 增加好感度并记录
        self.achievement_manager.add_favorability(event["favorability_gain"])
        self.achievement_manager.trigger_season_event(selected_season)

        return event, selected_season

class WindGameGUI:
    """风之棋游戏图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("风棋少女 - 完整版")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        # 游戏状态
        self.achievement_manager = AchievementManager()
        self.tip_manager = GameTips()
        self.current_window = None

        # 创建主菜单
        self.show_main_menu()

    def show_main_menu(self):
        """显示主菜单"""
        if self.current_window:
            self.current_window.destroy()

        self.current_window = tk.Frame(self.root, bg="#f0f0f0")
        self.current_window.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = tk.Label(
            self.current_window,
            text=" 风棋少女 ",
            font=("微软雅黑", 32, "bold"),
            bg="#f0f0f0",
            fg="#1eaef6"
        )
        title_label.pack(pady=20)

        # 统计信息
        special_events_count = self.achievement_manager.get_special_events_count()
        favorability = self.achievement_manager.get_favorability()

        stats_frame = tk.Frame(self.current_window, bg="#fff0f5", relief=tk.RAISED, borderwidth=2)
        stats_frame.pack(pady=10, padx=50, fill=tk.X)

        tk.Label(
            stats_frame,
            text=f"已解锁特殊结局: {special_events_count}/2",
            font=("微软雅黑", 12),
            bg="#fff0f5",
            fg="#333"
        ).pack(pady=5)

        tk.Label(
            stats_frame,
            text=f"当前好感度: {favorability}",
            font=("微软雅黑", 12),
            bg="#fff0f5",
            fg="#333"
        ).pack(pady=5)

        # 提示
        tip_label = tk.Label(
            self.current_window,
            text=f"💡 {self.tip_manager.get_random_tip()}",
            font=("微软雅黑", 10),
            bg="#fffde7",
            fg="#666",
            wraplength=600,
            justify=tk.CENTER
        )
        tip_label.pack(pady=10, padx=50)

        # 菜单按钮
        button_frame = tk.Frame(self.current_window, bg="#f0f0f0")
        button_frame.pack(pady=20)

        buttons = [
            ("🎓 新手介绍模式", lambda: self.select_board_size(GameMode.TUTORIAL)),
            ("👥 双人对战模式", lambda: self.select_board_size(GameMode.PVP)),
            ("💕 美少女对战模式", lambda: self.select_board_size(GameMode.PVE)),
            ("💬 与风子聊天", self.show_chat),
            ("⚙️ 游戏设置", self.show_settings),
            ("🚪 退出游戏", self.root.quit)
        ]

        for text, command in buttons:
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                font=("微软雅黑", 12),
                bg="#1eaef6",
                fg="white",
                width=25,
                height=2,
                cursor="hand2",
                relief=tk.RAISED,
                borderwidth=3
            )
            btn.pack(pady=5)

        # 制作人员
        credits_label = tk.Label(
            self.current_window,
            text="制作：常乐风 | 只为博君一笑，不必照单全收",
            font=("微软雅黑", 9),
            bg="#f0f0f0",
            fg="#999"
        )
        credits_label.pack(side=tk.BOTTOM, pady=10)

    def select_board_size(self, game_mode):
        """选择棋盘尺寸"""
        if self.current_window:
            self.current_window.destroy()

        self.current_window = tk.Frame(self.root, bg="#f0f0f0")
        self.current_window.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            self.current_window,
            text="选择棋盘尺寸",
            font=("微软雅黑", 24, "bold"),
            bg="#f0f0f0",
            fg="#1eaef6"
        ).pack(pady=20)

        size_frame = tk.Frame(self.current_window, bg="#f0f0f0")
        size_frame.pack(pady=20)

        sizes = [
            (BoardSize.SMALL, "小棋盘 (5×5, 每方4个棋子)"),
            (BoardSize.MEDIUM, "中棋盘 (9×9, 每方6个棋子)"),
            (BoardSize.LARGE, "大棋盘 (16×16, 每方8个棋子)")
        ]

        for board_size, text in sizes:
            btn = tk.Button(
                size_frame,
                text=text,
                command=lambda bs=board_size, gm=game_mode: self.start_game(gm, bs),
                font=("微软雅黑", 12),
                bg="#87ceeb",
                fg="white",
                width=35,
                height=2,
                cursor="hand2"
            )
            btn.pack(pady=10)

        tk.Button(
            self.current_window,
            text="返回主菜单",
            command=self.show_main_menu,
            font=("微软雅黑", 12),
            bg="#ccc",
            fg="black",
            width=15,
            height=1,
            cursor="hand2"
        ).pack(pady=20)

    def start_game(self, game_mode, board_size):
        """开始游戏"""
        if self.current_window:
            self.current_window.destroy()

        if game_mode == GameMode.TUTORIAL:
            self.show_tutorial(board_size)
        else:
            game_window = GameWindow(self.root, game_mode, board_size, self.achievement_manager, self.show_main_menu)
            self.current_window = game_window.frame

    def show_tutorial(self, board_size):
        """显示教程"""
        if self.current_window:
            self.current_window.destroy()

        self.current_window = tk.Frame(self.root, bg="#f0f0f0")
        self.current_window.pack(fill=tk.BOTH, expand=True)

        # 简化版教程窗口
        tutorial_text = tk.Text(
            self.current_window,
            font=("微软雅黑", 12),
            wrap=tk.WORD,
            height=15,
            width=60
        )
        tutorial_text.pack(pady=20, padx=20)

        tutorial_content = """ 欢迎来到风之棋的世界！

我是风子，今天由我来教你玩这个有趣的游戏～

【认识棋盘】
棋盘由许多方格组成，每个位置都有坐标。

【了解棋子】
游戏有两种棋子：黑色圆点●代表你（玩家A），白色圆点○代表我（玩家B）。

【风的规则】
风之棋最特别的地方就是'风'的规则！棋子必须按照风向移动。

【移动规则】
移动棋子时，你需要选择起始位置和目标位置。

【如何获胜】
获胜条件：把自己的3个棋子连成一条直线！

【高级策略】
控制风眼是关键！风眼上的棋子可以自由移动，非常强大。
"""

        tutorial_text.insert(tk.END, tutorial_content)
        tutorial_text.config(state=tk.DISABLED)

        tk.Button(
            self.current_window,
            text="返回主菜单",
            command=self.show_main_menu,
            font=("微软雅黑", 12),
            bg="#1eaef6",
            fg="white",
            width=15,
            height=2,
            cursor="hand2"
        ).pack(pady=20)

    def show_chat(self):
        """显示聊天界面"""
        if self.current_window:
            self.current_window.destroy()

        chat_window = ChatWindow(self.root, self.achievement_manager, self.show_main_menu)
        self.current_window = chat_window.frame

    def show_settings(self):
        """显示设置界面"""
        if self.current_window:
            self.current_window.destroy()

        settings_window = SettingsWindow(self.root, self.achievement_manager, self.show_main_menu)
        self.current_window = settings_window.frame

class GameWindow:
    """游戏窗口"""

    def __init__(self, root, game_mode, board_size, achievement_manager, back_callback):
        self.root = root
        self.game_mode = game_mode
        self.board_size_value = board_size.value[0]
        self.pieces_per_player = board_size.value[2]
        self.board_name = board_size.value[3]
        self.board_size_enum = board_size
        self.achievement_manager = achievement_manager
        self.back_callback = back_callback

        # 初始化游戏状态
        self.board = [[None for _ in range(self.board_size_value)] for _ in range(self.board_size_value)]
        self.wind_direction = random.choice(list(WindDirection))
        self.wind_duration = 1
        self.max_wind_duration = 3
        self.current_player = Player.A
        self.game_over = False
        self.winner = None
        self.move_count = 0
        self.selected_piece = None
        self.valid_moves = []

        # AI和美少女
        if game_mode == GameMode.PVE:
            self.beauty_girl = ACGNBeautyGirl()
            self.ai = WindGameAI(difficulty="medium")
            self.season_event_manager = SeasonEventManager(achievement_manager)
        else:
            self.beauty_girl = None
            self.ai = None
            self.season_event_manager = None

        # 初始化棋盘
        self.initialize_board()

        # 创建界面
        self.frame = tk.Frame(self.root, bg="#f0f0f0")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()
        self.update_display()

    def initialize_board(self):
        """初始化棋盘"""
        size = self.board_size_value
        pieces = self.pieces_per_player

        a_positions = []
        step = max(1, size // (pieces + 1))
        for i in range(pieces):
            pos = i * step + step // 2
            if pos >= size:
                pos = size - 1 - (i % (size // 2))
            a_positions.append((pos, 0))

        for x, y in a_positions:
            self.board[y][x] = Player.A

        b_positions = []
        for i in range(pieces):
            pos = i * step + step // 2
            if pos >= size:
                pos = size - 1 - (i % (size // 2))
            b_positions.append((pos, size-1))

        for x, y in b_positions:
            self.board[y][x] = Player.B

    def create_widgets(self):
        """创建界面组件"""
        # 顶部信息栏
        info_frame = tk.Frame(self.frame, bg="#e6e6fa", relief=tk.RAISED, borderwidth=2)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.info_label = tk.Label(
            info_frame,
            text="",
            font=("微软雅黑", 11),
            bg="#e6e6fa",
            fg="#333"
        )
        self.info_label.pack(pady=5)

        # 主容器
        main_container = tk.Frame(self.frame, bg="#f0f0f0")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 棋盘画布
        self.canvas_frame = tk.Frame(main_container, bg="#f0f0f0")
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", relief=tk.SUNKEN, borderwidth=2)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # 右侧面板
        right_panel = tk.Frame(main_container, bg="#f0f0f0", width=250)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        # 对话区域
        tk.Label(
            right_panel,
            text="💬 对话",
            font=("微软雅黑", 12, "bold"),
            bg="#f0f0f0",
            fg="#ff69b4"
        ).pack(pady=(0, 5))

        self.dialogue_text = scrolledtext.ScrolledText(
            right_panel,
            font=("微软雅黑", 10),
            wrap=tk.WORD,
            height=15,
            width=30,
            bg="#fffde7"
        )
        self.dialogue_text.pack(pady=5, padx=5, fill=tk.BOTH, expand=False)
        self.dialogue_text.config(state=tk.DISABLED)

        # 操作提示
        tk.Label(
            right_panel,
            text="📖 操作提示",
            font=("微软雅黑", 12, "bold"),
            bg="#f0f0f0",
            fg="#1eaef6"
        ).pack(pady=(10, 5))

        help_text = tk.Text(
            right_panel,
            font=("微软雅黑", 9),
            wrap=tk.WORD,
            height=8,
            width=30,
            bg="#e6f3ff",
            relief=tk.FLAT
        )
        help_text.pack(pady=5, padx=5)

        help_content = """点击你的棋子选中，然后点击有效位置移动。

★ 是风眼，可以自由移动。

风向决定了棋子可以移动的方向：
- 水平风：左右移动
- 垂直风：上下移动
- 旋风：斜向移动

获胜条件：3个棋子连成直线！
"""
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)

        # 按钮
        button_frame = tk.Frame(right_panel, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="返回主菜单",
            command=self.back_callback,
            font=("微软雅黑", 10),
            bg="#ccc",
            fg="black",
            width=20,
            height=1,
            cursor="hand2"
        ).pack(pady=5)

    def on_canvas_resize(self, event):
        """画布大小改变时重绘"""
        self.draw_board()

    def draw_board(self):
        """绘制棋盘"""
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or height < 100:
            return

        # 计算单元格大小
        cell_size = min(width // (self.board_size_value + 2), height // (self.board_size_value + 2))
        offset_x = (width - cell_size * self.board_size_value) // 2
        offset_y = (height - cell_size * self.board_size_value) // 2

        # 绘制网格
        for i in range(self.board_size_value + 1):
            # 横线
            self.canvas.create_line(
                offset_x, offset_y + i * cell_size,
                offset_x + self.board_size_value * cell_size, offset_y + i * cell_size,
                fill="#ccc", width=1
            )
            # 竖线
            self.canvas.create_line(
                offset_x + i * cell_size, offset_y,
                offset_x + i * cell_size, offset_y + self.board_size_value * cell_size,
                fill="#ccc", width=1
            )

        # 绘制风眼
        center = self.board_size_value // 2
        center_x = offset_x + center * cell_size + cell_size // 2
        center_y = offset_y + center * cell_size + cell_size // 2
        self.canvas.create_oval(
            center_x - cell_size // 3, center_y - cell_size // 3,
            center_x + cell_size // 3, center_y + cell_size // 3,
            fill="#ffd700", outline="#ff8c00", width=2
        )

        # 绘制棋子
        for y in range(self.board_size_value):
            for x in range(self.board_size_value):
                piece = self.board[y][x]
                if piece:
                    px = offset_x + x * cell_size + cell_size // 2
                    py = offset_y + y * cell_size + cell_size // 2
                    radius = cell_size // 2 - 2

                    color = "#000000" if piece == Player.A else "#ffffff"
                    outline_color = "#333333"

                    self.canvas.create_oval(
                        px - radius, py - radius,
                        px + radius, py + radius,
                        fill=color, outline=outline_color, width=2
                    )

        # 高亮选中的棋子
        if self.selected_piece:
            x, y = self.selected_piece
            px = offset_x + x * cell_size + cell_size // 2
            py = offset_y + y * cell_size + cell_size // 2
            self.canvas.create_oval(
                px - cell_size // 2, py - cell_size // 2,
                px + cell_size // 2, py + cell_size // 2,
                outline="#1eaef6", width=4
            )

        # 高亮有效移动
        for x, y in self.valid_moves:
            px = offset_x + x * cell_size + cell_size // 2
            py = offset_y + y * cell_size + cell_size // 2
            self.canvas.create_oval(
                px - 5, py - 5,
                px + 5, py + 5,
                fill="#1eaef6", outline=""
            )

        # 保存位置信息
        self.board_offset_x = offset_x
        self.board_offset_y = offset_y
        self.cell_size = cell_size

    def on_canvas_click(self, event):
        """处理棋盘点击"""
        if self.game_over:
            return

        if self.game_mode == GameMode.PVE and self.current_player == Player.B:
            return  # AI的回合

        x = (event.x - self.board_offset_x) // self.cell_size
        y = (event.y - self.board_offset_y) // self.cell_size

        if not (0 <= x < self.board_size_value and 0 <= y < self.board_size_value):
            return

        # 如果已选中棋子，尝试移动
        if self.selected_piece:
            if (x, y) in self.valid_moves:
                self.move_piece(self.selected_piece, (x, y))
            elif self.board[y][x] == self.current_player:
                # 选择另一个棋子
                self.select_piece((x, y))
            else:
                # 取消选择
                self.selected_piece = None
                self.valid_moves = []
        else:
            # 选择棋子
            if self.board[y][x] == self.current_player:
                self.select_piece((x, y))

        self.draw_board()

    def select_piece(self, pos):
        """选择棋子"""
        self.selected_piece = pos
        self.valid_moves = self.get_valid_moves(pos)

    def get_valid_moves(self, piece_pos):
        """获取合法移动"""
        x, y = piece_pos
        player = self.board[y][x]
        if not player:
            return []

        valid_moves = []
        center = self.board_size_value // 2

        if (x, y) == (center, center):
            directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        elif self.wind_direction == WindDirection.HORIZONTAL:
            directions = [(-1,0), (1,0)]
        elif self.wind_direction == WindDirection.VERTICAL:
            directions = [(0,-1), (0,1)]
        elif self.wind_direction == WindDirection.DIAGONAL:
            directions = [(-1,-1), (-1,1), (1,-1), (1,1)]

        for dx, dy in directions:
            step = 1
            while True:
                nx, ny = x + dx*step, y + dy*step
                if not (0 <= nx < self.board_size_value and 0 <= ny < self.board_size_value):
                    break
                if self.board[ny][nx] is not None:
                    break
                valid_moves.append((nx, ny))
                step += 1

        return valid_moves

    def move_piece(self, from_pos, to_pos, is_ai=False):
        """移动棋子"""
        from_x, from_y = from_pos
        to_x, to_y = to_pos

        self.board[to_y][to_x] = self.board[from_y][from_x]
        self.board[from_y][from_x] = None
        self.move_count += 1
        self.selected_piece = None
        self.valid_moves = []

        # 显示对话
        if self.game_mode == GameMode.PVE and self.beauty_girl:
            if not is_ai and self.current_player == Player.A:
                move_quality = self._evaluate_move_quality(from_pos, to_pos, Player.A)
                if move_quality > 0:
                    self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('player_good_move'))
                else:
                    self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('player_bad_move'))

            elif is_ai and self.current_player == Player.B:
                move_quality = self._evaluate_move_quality(from_pos, to_pos, Player.B)
                if move_quality > 0:
                    self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('good_ai_move'))
                else:
                    self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('bad_ai_move'))

                if random.random() < 0.2:
                    self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('special_actions'))

        # 检查胜利条件
        if self.check_win(self.current_player):
            self.game_over = True
            self.winner = self.current_player

            if self.game_mode == GameMode.PVE and self.achievement_manager:
                player_won = self.winner == Player.A
                self.achievement_manager.record_game_result(self.board_size_enum, player_won)

                all_win_condition, all_lose_condition = self.achievement_manager.check_special_event_conditions()

                if all_win_condition and player_won:
                    self.show_special_win_event()
                    return
                elif all_lose_condition and not player_won:
                    self.show_special_lose_event()
                    return
                else:
                    if self.game_mode == GameMode.PVE and self.beauty_girl:
                        if self.winner == Player.B:
                            self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('victory'))
                            self.beauty_girl.update_relationship(False)
                        else:
                            self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('defeat'))
                            self.beauty_girl.update_relationship(True)

            self.show_game_over()
            return

        self.current_player = Player.B if self.current_player == Player.A else Player.A
        self.change_wind()
        self.update_display()

        # AI回合
        if self.game_mode == GameMode.PVE and self.current_player == Player.B and not self.game_over:
            self.root.after(1500, self.ai_move)

    def _evaluate_move_quality(self, from_pos, to_pos, player):
        """评估移动质量"""
        to_x, to_y = to_pos
        center = self.board_size_value // 2

        distance_to_center = abs(to_x - center) + abs(to_y - center)
        quality = (self.board_size_value - distance_to_center) * 2

        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx1, ny1 = to_x + dx, to_y + dy
                nx2, ny2 = to_x - dx, to_y - dy

                if 0 <= nx1 < self.board_size_value and 0 <= ny1 < self.board_size_value and self.board[ny1][nx1] == player:
                    quality += 5
                if 0 <= nx2 < self.board_size_value and 0 <= ny2 < self.board_size_value and self.board[ny2][nx2] == player:
                    quality += 5

        return quality

    def check_win(self, player):
        """检查是否获胜"""
        size = self.board_size_value

        for y in range(size):
            for x in range(size - 2):
                line = [(x+i, y) for i in range(3)]
                if all(self.board[y][x+i] == player for i in range(3)):
                    bottom_line = 0 if player == Player.A else size-1
                    bottom_count = sum(1 for x, y in line if y == bottom_line)
                    if bottom_count <= 1:
                        return True

        for x in range(size):
            for y in range(size - 2):
                line = [(x, y+i) for i in range(3)]
                if all(self.board[y+i][x] == player for i in range(3)):
                    bottom_line = 0 if player == Player.A else size-1
                    bottom_count = sum(1 for x, y in line if y == bottom_line)
                    if bottom_count <= 1:
                        return True

        for x in range(size - 2):
            for y in range(size - 2):
                line = [(x+i, y+i) for i in range(3)]
                if all(self.board[y+i][x+i] == player for i in range(3)):
                    bottom_line = 0 if player == Player.A else size-1
                    bottom_count = sum(1 for x, y in line if y == bottom_line)
                    if bottom_count <= 1:
                        return True

        for x in range(2, size):
            for y in range(size - 2):
                line = [(x-i, y+i) for i in range(3)]
                if all(self.board[y+i][x-i] == player for i in range(3)):
                    bottom_line = 0 if player == Player.A else size-1
                    bottom_count = sum(1 for x, y in line if y == bottom_line)
                    if bottom_count <= 1:
                        return True

        return False

    def change_wind(self):
        """改变风向"""
        if self.wind_duration < self.max_wind_duration and random.random() < 0.7:
            self.wind_duration += 1
        else:
            self.wind_direction = random.choice(list(WindDirection))
            self.wind_duration = 1

            if self.game_mode == GameMode.PVE and self.beauty_girl and self.current_player == Player.B:
                self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('wind_change'))

    def ai_move(self):
        """AI移动"""
        game_state = {
            "board": self.board,
            "board_size": self.board_size_value,
            "current_player": self.current_player,
            "wind_direction": self.wind_direction
        }

        best_move = self.ai.find_best_move(game_state)
        if best_move:
            from_pos, to_pos = best_move
            self.add_dialogue(self.beauty_girl.name, self.beauty_girl.get_dialogue('my_turn'))
            self.move_piece(from_pos, to_pos, is_ai=True)

        self.draw_board()

    def update_display(self):
        """更新显示"""
        current_player_text = "你(●)" if self.current_player == Player.A else f"{self.beauty_girl.name}(○)" if self.beauty_girl else "玩家B(○)"

        info_text = f"回合: {self.move_count} | 棋盘: {self.board_name} | 风向: {self.wind_direction.value} ({self.wind_duration}/3) | 当前玩家: {current_player_text}"
        self.info_label.config(text=info_text)

        self.draw_board()

    def add_dialogue(self, speaker, text):
        """添加对话"""
        self.dialogue_text.config(state=tk.NORMAL)
        self.dialogue_text.insert(tk.END, f"\n[{speaker}]: {text}\n")
        self.dialogue_text.see(tk.END)
        self.dialogue_text.config(state=tk.DISABLED)

    def show_game_over(self):
        """显示游戏结束"""
        winner_text = "🏆 恭喜！你获胜！" if self.winner == Player.A else "😢 遗憾！对手获胜！"

        # 添加游戏结束信息
        self.add_dialogue("系统", f"游戏结束！{winner_text}")
        self.add_dialogue("系统", f"总回合数: {self.move_count} | 棋盘: {self.board_name}")

        # 检查季节事件
        if self.game_mode == GameMode.PVE and random.random() < 0.3:
            event_result = self.season_event_manager.check_and_trigger_event()
            if event_result:
                event, season = event_result
                self.show_season_event(event, season)

    def show_season_event(self, event, season):
        """显示季节事件"""
        event_window = tk.Toplevel(self.root)
        event_window.title(event['title'])
        event_window.geometry("500x400")

        content_frame = tk.Frame(event_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(
            content_frame,
            text=event['title'],
            font=("微软雅黑", 16, "bold"),
            fg="#1eaef6"
        ).pack(pady=10)

        tk.Label(
            content_frame,
            text=event['description'],
            font=("微软雅黑", 11),
            wraplength=450
        ).pack(pady=10)

        event_text = scrolledtext.ScrolledText(content_frame, font=("微软雅黑", 10), wrap=tk.WORD, height=10)
        event_text.pack(pady=10, fill=tk.BOTH, expand=True)

        for scene in event['scenes']:
            event_text.insert(tk.END, scene + "\n\n")

        event_text.config(state=tk.DISABLED)

        # 风子的对话
        dialogue_text = event["title"].split()[1]
        fengzi_speech = f"和前辈一起的{dialogue_text}，我会一直记住的！"

        tk.Label(
            content_frame,
            text=f"[风子]: {fengzi_speech}",
            font=("微软雅黑", 11, "bold"),
            fg="#ff69b4",
            wraplength=450
        ).pack(pady=10)

        tk.Label(
            content_frame,
            text=f"🎉 好感度 +{event['favorability_gain']}！",
            font=("微软雅黑", 11),
            fg="#ff4500"
        ).pack(pady=5)

        tk.Button(
            content_frame,
            text="继续",
            command=event_window.destroy,
            font=("微软雅黑", 12),
            bg="#ff69b4",
            fg="white",
            width=15
        ).pack(pady=10)

    def show_special_win_event(self):
        """显示特殊胜利事件"""
        self.achievement_manager.trigger_special_event("all_win")

        event_window = tk.Toplevel(self.root)
        event_window.title("特殊剧情 - 风子的赌气")
        event_window.geometry("600x500")

        content_frame = tk.Frame(event_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(
            content_frame,
            text="🎭 特殊剧情触发 - 风子的赌气 🎭",
            font=("微软雅黑", 14, "bold"),
            fg="#ff69b4"
        ).pack(pady=10)

        tk.Label(
            content_frame,
            text=f"当前好感度: {self.achievement_manager.get_favorability()}",
            font=("微软雅黑", 11)
        ).pack(pady=5)

        event_text = scrolledtext.ScrolledText(content_frame, font=("微软雅黑", 11), wrap=tk.WORD, height=12)
        event_text.pack(pady=10, fill=tk.BOTH, expand=True)

        event_content = """[第一天]

风子：哼！讨厌的前辈！我再也不理你了！
（但她的眼神中透露着一丝不舍）


[第二天]

你来到风棋社，发现风子已经坐在棋盘前等着你。

风子：...前辈真是的，昨天说的话不算数！
风子：今天一定要赢回来！不过...今天可以下慢一点...
风子：（小声）想和前辈多待一会儿...
"""

        event_text.insert(tk.END, event_content)
        event_text.config(state=tk.DISABLED)

        tk.Button(
            content_frame,
            text="继续",
            command=event_window.destroy,
            font=("微软雅黑", 12),
            bg="#ff69b4",
            fg="white",
            width=15
        ).pack(pady=10)

    def show_special_lose_event(self):
        """显示特殊失败事件"""
        self.achievement_manager.trigger_special_event("all_lose")

        event_window = tk.Toplevel(self.root)
        event_window.title("特殊剧情 - 风子的告白")
        event_window.geometry("600x600")

        content_frame = tk.Frame(event_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(
            content_frame,
            text="💕 特殊剧情触发 - 风子的告白 💕",
            font=("微软雅黑", 14, "bold"),
            fg="#ff69b4"
        ).pack(pady=10)

        tk.Label(
            content_frame,
            text=f"当前好感度: {self.achievement_manager.get_favorability()}",
            font=("微软雅黑", 11)
        ).pack(pady=5)

        event_text = scrolledtext.ScrolledText(content_frame, font=("微软雅黑", 11), wrap=tk.WORD, height=18)
        event_text.pack(pady=10, fill=tk.BOTH, expand=True)

        event_content = """[风棋社，黄昏]

夕阳透过窗户洒在棋盘上，风子低着头，手指轻轻摩挲着棋子。


风子：前辈...其实我一直想告诉你...
（风子停顿了一下，脸微微泛红）

风子：虽然我总是输给前辈，但我真的很开心...
（她的声音越来越小，眼眶开始泛红）

风子：前辈...我...我喜欢你！
（风子猛地抬起头，脸已经红得像苹果一样）

风子：从第一次和前辈下棋开始，我就一直喜欢着前辈...
（眼泪在眼眶中打转，她努力不让它们掉下来）

风子：我知道我很笨，总是输给前辈...

风子：但是...但是和前辈在一起的时间，是我最开心的时候...


（风子的声音越来越小，脸已经红得像苹果一样）
（眼泪在她的眼眶中打转，但她努力不让它们掉下来）
（你一时不知道说什么好，只是静静地看着她）
"""

        event_text.insert(tk.END, event_content)
        event_text.config(state=tk.DISABLED)

        tk.Button(
            content_frame,
            text="继续",
            command=event_window.destroy,
            font=("微软雅黑", 12),
            bg="#ff69b4",
            fg="white",
            width=15
        ).pack(pady=10)

class ChatWindow:
    """聊天窗口"""

    def __init__(self, root, achievement_manager, back_callback):
        self.root = root
        self.achievement_manager = achievement_manager
        self.back_callback = back_callback
        self.beauty_girl = ACGNBeautyGirl()
        self.chat_system = ChatSystem(achievement_manager)

        self.frame = tk.Frame(root, bg="#f0f0f0")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()
        self.start_new_topic()

    def create_widgets(self):
        """创建界面"""
        tk.Label(
            self.frame,
            text="🎤 与风子聊天 🎤",
            font=("微软雅黑", 20, "bold"),
            bg="#f0f0f0",
            fg="#ff69b4"
        ).pack(pady=15)

        # 统计信息
        stats_frame = tk.Frame(self.frame, bg="#fff0f5", relief=tk.RAISED, borderwidth=2)
        stats_frame.pack(pady=10, padx=50)

        current_favorability = self.achievement_manager.get_favorability()

        tk.Label(
            stats_frame,
            text=f"当前好感度: {current_favorability}",
            font=("微软雅黑", 12),
            bg="#fff0f5"
        ).pack(pady=5)

        tk.Label(
            stats_frame,
            text=f"风子心情: {self.beauty_girl.get_emotional_state()}",
            font=("微软雅黑", 12),
            bg="#fff0f5"
        ).pack(pady=5)

        # 对话显示区域
        self.chat_display = scrolledtext.ScrolledText(
            self.frame,
            font=("微软雅黑", 11),
            wrap=tk.WORD,
            height=15,
            width=60,
            bg="#fffde7"
        )
        self.chat_display.pack(pady=10, padx=50)
        self.chat_display.config(state=tk.DISABLED)

        # 选项按钮区域
        self.options_frame = tk.Frame(self.frame, bg="#f0f0f0")
        self.options_frame.pack(pady=10)

        # 按钮
        button_frame = tk.Frame(self.frame, bg="#f0f0f0")
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="返回主菜单",
            command=self.back_callback,
            font=("微软雅黑", 11),
            bg="#ccc",
            fg="black",
            width=15,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        self.next_topic_btn = tk.Button(
            button_frame,
            text="下一个话题",
            command=self.start_new_topic,
            font=("微软雅黑", 11),
            bg="#87ceeb",
            fg="white",
            width=15,
            cursor="hand2"
        )
        self.next_topic_btn.pack(side=tk.LEFT, padx=10)

    def start_new_topic(self):
        """开始新话题"""
        # 清空选项
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        # 随机选择一个话题
        topic_key = random.choice(list(self.chat_system.topics.keys()))
        topic = self.chat_system.topics[topic_key]

        # 显示问题
        self.add_message(self.beauty_girl.name, topic["question"])

        # 创建选项按钮
        for i, (response_text, favorability_change, reaction) in enumerate(topic["responses"]):
            btn = tk.Button(
                self.options_frame,
                text=f"{i+1}. {response_text}",
                command=lambda rt=response_text, fc=favorability_change, r=reaction: self.handle_choice(rt, fc, r),
                font=("微软雅黑", 10),
                bg="#e6e6fa",
                fg="black",
                width=40,
                cursor="hand2"
            )
            btn.pack(pady=3)

    def handle_choice(self, response_text, favorability_change, reaction):
        """处理选择"""
        # 清空选项
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        # 显示玩家选择
        self.add_message("你", response_text)

        # 显示风子反应
        self.add_message(self.beauty_girl.name, reaction)

        # 更新好感度
        if favorability_change != 0:
            self.achievement_manager.add_favorability(favorability_change)
            if favorability_change > 0:
                self.add_message("系统", f"🎉 好感度 +{favorability_change}！")
            else:
                self.add_message("系统", f"😢 好感度 {favorability_change}！")

        # 显示当前好感度
        new_favorability = self.achievement_manager.get_favorability()
        self.add_message("系统", f"当前好感度: {new_favorability}")

        # 20%几率触发额外对话
        if random.random() < 0.2:
            daily_topic = random.choice(self.chat_system.daily_topics)
            self.add_message(self.beauty_girl.name, daily_topic)

    def add_message(self, speaker, text):
        """添加消息"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n[{speaker}]: {text}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

class SettingsWindow:
    """设置窗口"""

    def __init__(self, root, achievement_manager, back_callback):
        self.root = root
        self.achievement_manager = achievement_manager
        self.back_callback = back_callback

        self.frame = tk.Frame(root, bg="#f0f0f0")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.create_widgets()

    def create_widgets(self):
        """创建界面"""
        tk.Label(
            self.frame,
            text="⚙️ 游戏设置 ⚙️",
            font=("微软雅黑", 20, "bold"),
            bg="#f0f0f0",
            fg="#1eaef6"
        ).pack(pady=15)

        # 统计信息
        self.create_stats_section()

        # 设置选项
        self.create_settings_section()

        # 按钮
        button_frame = tk.Frame(self.frame, bg="#f0f0f0")
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="返回主菜单",
            command=self.back_callback,
            font=("微软雅黑", 11),
            bg="#ccc",
            fg="black",
            width=15,
            cursor="hand2"
        ).pack()

    def create_stats_section(self):
        """创建统计信息部分"""
        stats_frame = tk.LabelFrame(
            self.frame,
            text="🎮 游戏统计",
            font=("微软雅黑", 12, "bold"),
            bg="#f0f0f0",
            fg="#666",
            relief=tk.GROOVE,
            borderwidth=2
        )
        stats_frame.pack(pady=10, padx=50, fill=tk.X)

        achievements = self.achievement_manager.data["achievements"]

        stats_text = f"""总游戏次数: {achievements['total_games']}
胜利次数: {achievements['total_wins']}
失败次数: {achievements['total_losses']}
当前好感度: {achievements['favorability']}

5×5棋盘: {achievements['small_wins']}胜 {achievements['small_losses']}负
9×9棋盘: {achievements['medium_wins']}胜 {achievements['medium_losses']}负
16×16棋盘: {achievements['large_wins']}胜 {achievements['large_losses']}负"""

        tk.Label(
            stats_frame,
            text=stats_text,
            font=("微软雅黑", 10),
            bg="#f0f0f0",
            justify=tk.LEFT
        ).pack(pady=10, padx=10)

        # 特殊结局
        special_events = achievements["special_events_triggered"]
        special_text = "🎭 特殊结局解锁: {}/2\n".format(self.achievement_manager.get_special_events_count())

        if special_events["all_win_special"]:
            special_text += "  ✓ 已解锁: '风子的赌气'结局\n"
        if special_events["all_lose_special"]:
            special_text += "  ✓ 已解锁: '风子的告白'结局\n"

        tk.Label(
            stats_frame,
            text=special_text,
            font=("微软雅黑", 10),
            bg="#f0f0f0",
            fg="#ff69b4",
            justify=tk.LEFT
        ).pack(pady=5, padx=10)

        # 季节事件
        season_events = achievements["season_events"]
        season_text = "🌸 季节事件:\n"

        if season_events["spring"]:
            season_text += "  ✓ 春日赏樱\n"
        if season_events["summer"]:
            season_text += "  ✓ 夏日祭典\n"
        if season_events["autumn"]:
            season_text += "  ✓ 秋季露营\n"
        if season_events["winter"]:
            season_text += "  ✓ 冬季滑雪\n"

        if season_text == "🌸 季节事件:\n":
            season_text += "  暂无事件"

        tk.Label(
            stats_frame,
            text=season_text,
            font=("微软雅黑", 10),
            bg="#f0f0f0",
            fg="#ff6347",
            justify=tk.LEFT
        ).pack(pady=5, padx=10)

    def create_settings_section(self):
        """创建设置选项部分"""
        settings_frame = tk.LabelFrame(
            self.frame,
            text="⚙️ 设置选项",
            font=("微软雅黑", 12, "bold"),
            bg="#f0f0f0",
            fg="#666",
            relief=tk.GROOVE,
            borderwidth=2
        )
        settings_frame.pack(pady=10, padx=50, fill=tk.X)

        # 对话显示时间
        time_frame = tk.Frame(settings_frame, bg="#f0f0f0")
        time_frame.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(
            time_frame,
            text="对话显示时间 (秒):",
            font=("微软雅黑", 10),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT)

        current_time = self.achievement_manager.get_setting("dialogue_display_time")
        time_var = tk.IntVar(value=current_time)

        time_spinbox = tk.Spinbox(
            time_frame,
            from_=1,
            to=60,
            textvariable=time_var,
            width=10,
            font=("微软雅黑", 10)
        )
        time_spinbox.pack(side=tk.LEFT, padx=10)

        def save_time():
            new_time = time_var.get()
            self.achievement_manager.update_setting("dialogue_display_time", new_time)
            messagebox.showinfo("成功", f"对话显示时间已设置为{new_time}秒")

        tk.Button(
            time_frame,
            text="保存",
            command=save_time,
            font=("微软雅黑", 10),
            bg="#87ceeb",
            fg="white",
            cursor="hand2"
        ).pack(side=tk.LEFT)

        # 查看制作人员名单
        tk.Button(
            settings_frame,
            text="📋 查看制作人员名单",
            command=self.show_credits,
            font=("微软雅黑", 10),
            bg="#98fb98",
            fg="black",
            width=30,
            cursor="hand2"
        ).pack(pady=5)

        # 重置游戏数据
        tk.Button(
            settings_frame,
            text="⚠️ 重置游戏数据",
            command=self.reset_data,
            font=("微软雅黑", 10),
            bg="#ff6b6b",
            fg="white",
            width=30,
            cursor="hand2"
        ).pack(pady=5)

    def show_credits(self):
        """显示制作人员名单"""
        credits_window = tk.Toplevel(self.root)
        credits_window.title("制作人员名单")
        credits_window.geometry("400x300")

        content_frame = tk.Frame(credits_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(
            content_frame,
            text="感谢您游玩本游戏",
            font=("微软雅黑", 14, "bold"),
            fg="#1eaef6"
        ).pack(pady=10)

        tk.Label(
            content_frame,
            text="只为博君一笑，不必照单全收",
            font=("微软雅黑", 11),
            fg="#666"
        ).pack(pady=5)

        tk.Label(
            content_frame,
            text="制作人员名单",
            font=("微软雅黑", 12, "bold"),
            fg="#333"
        ).pack(pady=15)

        credits_text = """剧本：常乐风
程序：常乐风
导演：常乐风
制作人：常乐风"""

        tk.Label(
            content_frame,
            text=credits_text,
            font=("微软雅黑", 11),
            justify=tk.LEFT
        ).pack(pady=10)

        tk.Button(
            content_frame,
            text="关闭",
            command=credits_window.destroy,
            font=("微软雅黑", 11),
            bg="#ccc",
            fg="black",
            width=15
        ).pack(pady=15)

    def reset_data(self):
        """重置游戏数据"""
        result = messagebox.askyesno(
            "确认重置",
            "⚠️ 警告：这将删除所有游戏记录和成就！\n此操作不可撤销！\n\n确定要重置吗？"
        )

        if result:
            save_file = self.achievement_manager.save_file
            if os.path.exists(save_file):
                os.remove(save_file)

            messagebox.showinfo("成功", "游戏数据已重置！")

            # 刷新界面
            self.frame.destroy()
            settings_window = SettingsWindow(self.root, AchievementManager(), self.back_callback)
            self.frame = settings_window.frame

def main():
    """主函数"""
    root = tk.Tk()
    game = WindGameGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
