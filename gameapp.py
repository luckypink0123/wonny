
import streamlit as st
from openai import OpenAI
import json
import random


# ==========================================
# 1. 기본 페이지 설정
# ==========================================

st.set_page_config(
    page_title="극본 구성 요소 할리갈리",
    page_icon="🔔",
    layout="wide"
)


# ==========================================
# 2. 디자인 CSS
# ==========================================

st.markdown("""
<style>
    .stApp {
        background-color: #FFF8ED;
    }

    h1, h2, h3 {
        color: #5B4636;
    }

    .main-title {
        text-align: center;
        color: #654C3B;
        font-size: 38px;
        font-weight: bold;
        padding: 15px;
    }

    .sub-title {
        text-align: center;
        color: #A1846C;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .player-card {
        background-color: white;
        border: 3px solid #E8D9C6;
        border-radius: 18px;
        padding: 15px;
        text-align: center;
        min-height: 220px;
        box-shadow: 2px 3px 8px rgba(0,0,0,0.06);
        margin-bottom: 10px;
    }

    .active-player {
        border: 3px solid #F2A65A;
        background-color: #FFF0D9;
    }

    .card-content {
        background-color: #FFFCF6;
        border: 2px solid #E8D9C6;
        border-radius: 12px;
        min-height: 110px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 12px;
        font-size: 17px;
        font-weight: bold;
        color: #594638;
        word-break: keep-all;
        line-height: 1.5;
    }

    .empty-card {
        color: #B9AA99;
        font-weight: normal;
    }

    .turn-box {
        background-color: #FFF0D9;
        border: 2px solid #F2C58D;
        border-radius: 15px;
        padding: 18px;
        text-align: center;
        margin-bottom: 15px;
    }

    .message-box {
        background-color: white;
        border-radius: 12px;
        padding: 12px;
        text-align: center;
        color: #8B694D;
        margin: 10px 0;
    }

    div.stButton > button {
        border-radius: 12px;
        font-weight: bold;
    }

    .bell-text {
        font-size: 25px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. 사이드바 - API 키 입력 및 게임 설정
# ==========================================

st.sidebar.title("⚙️ 게임 설정")

api_key = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    placeholder="sk-...",
    help="본인의 OpenAI API 키를 입력하세요."
)

st.sidebar.caption(
    "🔒 API 키는 코드에 저장되지 않습니다."
)

st.sidebar.divider()

st.sidebar.subheader("🎮 참여 인원")

player_count = st.sidebar.selectbox(
    "게임에 참여할 인원",
    options=[2, 3, 4, 5, 6, 7, 8],
    index=2,
    format_func=lambda x: f"{x}명",
    disabled=st.session_state.get("game_started", False)
)

st.sidebar.caption(
    "총 48장의 카드를 참여 인원에게 최대한 균등하게 나눕니다."
)

st.sidebar.divider()

if st.sidebar.button("🔄 새 게임 준비", use_container_width=True):
    for key in [
        "game_started",
        "decks",
        "table_piles",
        "collected",
        "players",
        "current_turn",
        "game_message",
        "game_ended"
    ]:
        st.session_state.pop(key, None)

    st.rerun()


# ==========================================
# 4. AI 카드 생성 함수
# ==========================================

def generate_cards(api_key):

    client = OpenAI(api_key=api_key)

    prompt = """
당신은 초등학교 5학년 국어 교과 수업 자료를 만드는 전문가입니다.

극본의 구성 요소인 지문, 대사, 해설을 학습하기 위한
할리갈리 게임 카드 48장을 만들어 주세요.

카드는 다음과 같이 정확히 구성합니다.

[1] 구성 요소 카드 12장
- 지문 4장
- 대사 4장
- 해설 4장

[2] 설명 카드 18장
- 지문 설명 6장
- 대사 설명 6장
- 해설 설명 6장

[3] 예시 카드 18장
- 지문 예시 6장
- 대사 예시 6장
- 해설 예시 6장

각 카드에는 다음 세 가지 정보가 있어야 합니다.

1. type: 정답 구성 요소
   - 지문
   - 대사
   - 해설

2. kind: 카드 종류
   - 구성 요소
   - 설명
   - 예시

3. text: 학생에게 보여 줄 문장

[작성 기준]

- 초등학교 5학년 학생이 이해할 수 있는 쉬운 표현을 사용합니다.
- 지문은 인물의 표정, 행동, 말투 등을 나타냅니다.
- 대사는 극본에서 인물이 직접 하는 말입니다.
- 해설은 장면의 배경이나 상황 등을 설명합니다.
- 설명 카드에는 해당 구성 요소의 특징을 설명합니다.
- 예시 카드는 실제 극본에 나올 법한 문장으로 작성합니다.
- 카드 문장은 짧고 명확하게 작성합니다.
- 같은 문장을 반복하지 않습니다.
- 지문과 해설이 혼동되지 않도록 구분을 명확히 합니다.
- 대사에는 인물의 이름과 직접 하는 말을 포함해도 좋습니다.

반드시 아래 JSON 형식으로만 출력하세요.

{
  "cards": [
    {
      "type": "지문",
      "kind": "구성 요소",
      "text": "고개를 끄덕이며 웃는다."
    }
  ]
}

카드는 반드시 총 48장이어야 합니다.
JSON 이외의 설명은 출력하지 마세요.
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )

    result_text = response.output_text

    data = json.loads(result_text)

    cards = data["cards"]

    # 카드 수 검증
    if len(cards) != 48:
        raise ValueError(
            f"카드가 48장이 아닙니다. 현재 {len(cards)}장입니다."
        )

    valid_types = ["지문", "대사", "해설"]
    valid_kinds = ["구성 요소", "설명", "예시"]

    # 카드 형식 검증
    for card in cards:
        if card["type"] not in valid_types:
            raise ValueError("잘못된 구성 요소 카드가 있습니다.")

        if card["kind"] not in valid_kinds:
            raise ValueError("잘못된 카드 종류가 있습니다.")

        if not card.get("text"):
            raise ValueError("문장이 없는 카드가 있습니다.")

    # 카드 종류별 개수 검증
    expected = {
        ("구성 요소", "지문"): 4,
        ("구성 요소", "대사"): 4,
        ("구성 요소", "해설"): 4,

        ("설명", "지문"): 6,
        ("설명", "대사"): 6,
        ("설명", "해설"): 6,

        ("예시", "지문"): 6,
        ("예시", "대사"): 6,
        ("예시", "해설"): 6
    }

    actual = {}

    for card in cards:
        key = (card["kind"], card["type"])
        actual[key] = actual.get(key, 0) + 1

    if actual != expected:
        raise ValueError(
            "카드 종류별 개수가 정확하지 않습니다. 다시 생성해 주세요."
        )

    return cards


# ==========================================
# 5. 게임 초기화 및 카드 배분
# ==========================================

def initialize_game(cards, count):

    random.shuffle(cards)

    players = [
        f"플레이어 {i + 1}"
        for i in range(count)
    ]

    decks = [[] for _ in range(count)]
    table_piles = [[] for _ in range(count)]
    collected = [0 for _ in range(count)]

    # 48장을 참여 인원에게 순서대로 균등 배분
    for i, card in enumerate(cards):
        decks[i % count].append(card)

    st.session_state.players = players
    st.session_state.decks = decks
    st.session_state.table_piles = table_piles
    st.session_state.collected = collected

    st.session_state.current_turn = 0
    st.session_state.game_started = True
    st.session_state.game_ended = False

    st.session_state.game_message = (
        "게임을 시작합니다! 첫 번째 플레이어가 카드를 뒤집으세요."
    )


# ==========================================
# 6. 공개된 카드 확인
# ==========================================

def get_visible_cards():

    visible_cards = []

    for pile in st.session_state.table_piles:

        if len(pile) > 0:
            visible_cards.append(pile[-1])

    return visible_cards


# ==========================================
# 7. 같은 구성 요소인지 판정
# ==========================================

def is_match():

    visible_cards = get_visible_cards()

    # 최소 2장의 카드가 공개되어야 함
    if len(visible_cards) < 2:
        return False

    first_type = visible_cards[0]["type"]

    return all(
        card["type"] == first_type
        for card in visible_cards
    )


# ==========================================
# 8. 모든 카드가 소진되었는지 확인
# ==========================================

def all_decks_empty():

    return all(
        len(deck) == 0
        for deck in st.session_state.decks
    )


# ==========================================
# 9. 다음 차례 플레이어 찾기
# ==========================================

def find_next_player(start_index):

    decks = st.session_state.decks
    count = len(decks)

    for i in range(1, count + 1):

        next_index = (start_index + i) % count

        if len(decks[next_index]) > 0:
            return next_index

    return start_index


# ==========================================
# 10. 카드 뒤집기
# ==========================================

def draw_card(player_index):

    if st.session_state.game_ended:
        return

    if player_index != st.session_state.current_turn:
        st.session_state.game_message = (
            "아직 자신의 차례가 아닙니다!"
        )
        return

    deck = st.session_state.decks[player_index]

    if len(deck) == 0:
        st.session_state.game_message = (
            "더 이상 뒤집을 카드가 없습니다."
        )
        return

    # 카드 한 장 뒤집기
    card = deck.pop()

    st.session_state.table_piles[player_index].append(card)

    st.session_state.game_message = (
        f"{st.session_state.players[player_index]}이(가) "
        "카드를 뒤집었습니다."
    )

    # 다음 플레이어에게 차례 이동
    next_player = find_next_player(player_index)

    st.session_state.current_turn = next_player

    # 모든 카드가 소진되고 정답 조합이 없으면 종료
    if all_decks_empty() and not is_match():
        finish_game()


# ==========================================
# 11. 종 누르기
# ==========================================

def ring_bell(player_index):

    if st.session_state.game_ended:
        return

    if is_match():

        total_cards = 0

        # 테이블 위에 놓인 모든 카드 더미 획득
        for pile in st.session_state.table_piles:
            total_cards += len(pile)

        st.session_state.collected[player_index] += total_cards

        # 테이블 카드 더미 비우기
        st.session_state.table_piles = [
            [] for _ in st.session_state.players
        ]

        # 종을 누른 사람이 다음 차례
        st.session_state.current_turn = player_index

        st.session_state.game_message = (
            f"🎉 정답! {st.session_state.players[player_index]}이(가) "
            f"카드 {total_cards}장을 가져갔습니다!"
        )

        # 모든 카드가 소진되었다면 게임 종료
        if all_decks_empty():
            finish_game()

    else:

        st.session_state.game_message = (
            f"아쉽습니다! {st.session_state.players[player_index]}의 "
            "종 누르기: 아직 같은 구성 요소가 아닙니다."
        )


# ==========================================
# 12. 게임 종료 및 점수 계산
# ==========================================

def finish_game():

    st.session_state.game_ended = True
    st.session_state.game_started = False

    players = st.session_state.players
    decks = st.session_state.decks
    table_piles = st.session_state.table_piles
    collected = st.session_state.collected

    scores = []

    for i in range(len(players)):

        remaining_cards = (
            len(decks[i]) +
            len(table_piles[i])
        )

        total_score = collected[i] + remaining_cards

        scores.append(total_score)

    max_score = max(scores)

    winners = [
        players[i]
        for i, score in enumerate(scores)
        if score == max_score
    ]

    if len(winners) == 1:
        winner_message = (
            f"🏆 최종 우승자는 {winners[0]}입니다!"
        )
    else:
        winner_message = (
            f"🏆 공동 우승! {', '.join(winners)}"
        )

    st.session_state.game_message = (
        "🎊 게임 종료! " + winner_message
    )


# ==========================================
# 13. 점수판
# ==========================================

def show_scores():

    st.subheader("🏆 현재 점수")

    players = st.session_state.players
    decks = st.session_state.decks
    table_piles = st.session_state.table_piles
    collected = st.session_state.collected

    cols = st.columns(len(players))

    for i, col in enumerate(cols):

        remaining = (
            len(decks[i]) +
            len(table_piles[i])
        )

        score = collected[i] + remaining

        with col:

            st.metric(
                label=players[i],
                value=f"{score}장"
            )


# ==========================================
# 14. 플레이어 카드 화면
# ==========================================

def show_players():

    players = st.session_state.players
    decks = st.session_state.decks
    table_piles = st.session_state.table_piles

    current_turn = st.session_state.current_turn

    # 한 줄에 최대 4명씩 표시
    for start in range(0, len(players), 4):

        end = min(start + 4, len(players))

        cols = st.columns(4)

        for i in range(start, end):

            with cols[i - start]:

                is_active = (
                    i == current_turn and
                    not st.session_state.game_ended
                )

                if is_active:
                    st.markdown(
                        f"### ⭐ {players[i]}"
                    )
                else:
                    st.markdown(
                        f"### {players[i]}"
                    )

                st.caption(
                    f"남은 카드: {len(decks[i])}장"
                )

                pile = table_piles[i]

                if pile:

                    top_card = pile[-1]

                    st.markdown(
                        f"""
                        <div class="card-content">
                            {top_card["text"]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.caption(
                        f"테이블에 쌓인 카드: {len(pile)}장"
                    )

                else:

                    st.markdown(
                        """
                        <div class="card-content empty-card">
                            아직 뒤집은 카드가 없습니다.
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.caption("테이블에 쌓인 카드: 0장")

                # 카드 뒤집기 버튼
                draw_disabled = (
                    not is_active or
                    len(decks[i]) == 0 or
                    st.session_state.game_ended
                )

                if st.button(
                    "🃏 카드 뒤집기",
                    key=f"draw_{i}",
                    use_container_width=True,
                    disabled=draw_disabled
                ):

                    draw_card(i)
                    st.rerun()

                # 종 누르기 버튼
                bell_disabled = st.session_state.game_ended

                if st.button(
                    "🔔 종 치기!",
                    key=f"bell_{i}",
                    use_container_width=True,
                    disabled=bell_disabled
                ):

                    ring_bell(i)
                    st.rerun()

        st.write("")


# ==========================================
# 15. 메인 화면
# ==========================================

st.markdown(
    '<div class="main-title">🔔 극본 구성 요소 할리갈리</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">지문, 대사, 해설을 찾아라!</div>',
    unsafe_allow_html=True
)


# 게임 시작 전 화면
if not st.session_state.get("game_started", False) and not st.session_state.get("game_ended", False):

    st.markdown("---")

    st.markdown(
        """
        <div style="
            background-color:white;
            padding:25px;
            border-radius:18px;
            text-align:center;
        ">
            <h2>🎮 게임 준비</h2>
            <p>사이드바에서 OpenAI API Key를 입력하고</p>
            <p>참여 인원을 선택한 뒤 게임을 시작하세요.</p>
            <h3>🃏 총 48장의 카드</h3>
            <p>구성 요소 카드 12장 · 설명 카드 18장 · 예시 카드 18장</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    if st.button(
        "🎉 게임 시작하기",
        use_container_width=True,
        type="primary"
    ):

        if not api_key:

            st.error(
                "사이드바에 OpenAI API Key를 입력해 주세요."
            )

        else:

            try:

                with st.spinner(
                    "AI가 게임 카드 48장을 만들고 있습니다. 잠시 기다려 주세요..."
                ):

                    cards = generate_cards(api_key)

                initialize_game(cards, player_count)

                st.success("카드 준비가 완료되었습니다!")

                st.rerun()

            except Exception as e:

                st.error(
                    f"카드 생성 중 오류가 발생했습니다: {str(e)}"
                )


# 게임 진행 화면
if st.session_state.get("game_started", False):

    st.markdown("---")

    st.markdown(
        f"""
        <div class="turn-box">
            <h2>🎯 현재 차례</h2>
            <h1>{st.session_state.players[st.session_state.current_turn]}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="message-box">
            {st.session_state.game_message}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "공개된 카드의 정답 구성 요소가 모두 같으면 "
        "가장 먼저 종을 누르세요!"
    )

    show_players()

    st.markdown("---")

    show_scores()


# 게임 종료 화면
if st.session_state.get("game_ended", False):

    st.markdown("---")

    st.success(
        st.session_state.game_message
    )

    st.subheader("🏆 최종 결과")

    players = st.session_state.players
    decks = st.session_state.decks
    table_piles = st.session_state.table_piles
    collected = st.session_state.collected

    final_scores = []

    for i in range(len(players)):

        score = (
            collected[i] +
            len(decks[i]) +
            len(table_piles[i])
        )

        final_scores.append(score)

    ranking = sorted(
        zip(players, final_scores),
        key=lambda x: x[1],
        reverse=True
    )

    for rank, (name, score) in enumerate(ranking, start=1):

        if rank == 1:
            st.markdown(
                f"### 🥇 {rank}위 {name} - {score}장"
            )
        elif rank == 2:
            st.markdown(
                f"### 🥈 {rank}위 {name} - {score}장"
            )
        elif rank == 3:
            st.markdown(
                f"### 🥉 {rank}위 {name} - {score}장"
            )
        else:
            st.write(
                f"{rank}위 {name} - {score}장"
            )

    if st.button(
        "🔄 새 게임 시작",
        use_container_width=True
    ):

        for key in [
            "game_started",
            "decks",
            "table_piles",
            "collected",
            "players",
            "current_turn",
            "game_message",
            "game_ended"
        ]:
            st.session_state.pop(key, None)

        st.rerun()
