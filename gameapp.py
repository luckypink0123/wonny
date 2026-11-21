
import streamlit as st
import random
import json
import html
from openai import OpenAI

# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="극본 할리갈리",
    page_icon="🔔",
    layout="wide"
)

# OpenAI API KEY 입력
API_KEY = "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"

client = OpenAI(api_key=API_KEY)

COMPONENTS = ["지문", "대사", "해설"]

PLAYERS = [
    "1번 학생", "2번 학생", "3번 학생", "4번 학생",
    "5번 학생", "6번 학생", "7번 학생", "8번 학생"
]


# ==========================================
# 2. AI 카드 생성
# ==========================================

def make_cards():

    prompt = """
    너는 초등학교 5학년 국어 교사야.

    극본의 구성 요소를 학습하는 할리갈리 카드 48장을 만들어 줘.

    [카드 구성]

    1. 구성 요소 카드 12장
       지문 4장, 대사 4장, 해설 4장

    2. 설명 카드 18장
       지문 설명 6장, 대사 설명 6장, 해설 설명 6장

    3. 예시 카드 18장
       지문 예시 6장, 대사 예시 6장, 해설 예시 6장

    [개념]

    지문: 인물의 표정, 행동, 움직임, 말투 등을 나타내는 부분.
    대사: 극본에서 인물이 직접 하는 말.
    해설: 무대의 배경, 시간, 장소, 상황 등을 설명하는 부분.

    [작성 조건]

    1. 초등학교 5학년 수준으로 작성해.
    2. 설명은 짧고 명확하게 작성해.
    3. 예시는 실제 극본에서 사용할 수 있는 문장으로 작성해.
    4. 지문 예시는 반드시 괄호를 사용해.
    5. 대사 예시는 인물 이름과 말로 구성해.
    6. 해설 예시는 무대의 배경이나 상황을 설명해.
    7. 내용이 서로 중복되지 않도록 해.
    8. 구성 요소 카드의 content는 '지문', '대사', '해설' 중 하나만 사용해.

    반드시 다음 JSON 형식으로 출력해.

    {
      "cards": [
        {
          "type": "지문",
          "category": "구성요소",
          "content": "지문"
        },
        {
          "type": "지문",
          "category": "설명",
          "content": "인물의 행동이나 표정 등을 나타내는 부분"
        },
        {
          "type": "지문",
          "category": "예시",
          "content": "(민수가 깜짝 놀라 뒤로 물러선다.)"
        }
      ]
    }

    총 48장을 정확하게 만들어 줘.
    """

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )

    result = json.loads(response.output_text)
    cards = result["cards"]

    expected = {
        ("지문", "구성요소"): 4,
        ("대사", "구성요소"): 4,
        ("해설", "구성요소"): 4,
        ("지문", "설명"): 6,
        ("대사", "설명"): 6,
        ("해설", "설명"): 6,
        ("지문", "예시"): 6,
        ("대사", "예시"): 6,
        ("해설", "예시"): 6
    }

    if len(cards) != 48:
        raise ValueError("카드가 48장이 아닙니다.")

    for key, count in expected.items():

        actual = sum(
            1 for card in cards
            if (card["type"], card["category"]) == key
        )

        if actual != count:
            raise ValueError(f"{key} 카드 수가 맞지 않습니다.")

    random.shuffle(cards)

    return cards


# ==========================================
# 3. 게임 시작
# ==========================================

def start_game(player_count):

    cards = make_cards()

    # 선택한 인원수에 맞게 균등 배분
    decks = [[] for _ in range(player_count)]

    for i, card in enumerate(cards):
        decks[i % player_count].append(card)

    for deck in decks:
        random.shuffle(deck)

    st.session_state.player_count = player_count
    st.session_state.decks = decks

    # 각 참여자가 뒤집은 카드 더미
    st.session_state.table_piles = [
        [] for _ in range(player_count)
    ]

    st.session_state.turn = 0
    st.session_state.started = True
    st.session_state.game_over = False
    st.session_state.message = "게임을 시작합니다!"
    st.session_state.winner = None


# ==========================================
# 4. 다음 차례 정하기
# ==========================================

def next_turn(current):

    decks = st.session_state.decks
    player_count = st.session_state.player_count

    for step in range(1, player_count + 1):

        next_player = (current + step) % player_count

        if len(decks[next_player]) > 0:
            return next_player

    # 다른 참여자가 없으면 현재 참여자가 계속 진행
    return current


# ==========================================
# 5. 현재 보이는 카드 확인
# ==========================================

def get_visible_cards():

    visible = []

    for i, pile in enumerate(st.session_state.table_piles):

        if pile:
            visible.append({
                "player": i,
                "card": pile[-1]
            })

    return visible


# ==========================================
# 6. 종을 누를 수 있는지 확인
# ==========================================

def is_match():

    visible = get_visible_cards()

    if len(visible) < 2:
        return False

    types = [
        item["card"]["type"]
        for item in visible
    ]

    return len(set(types)) == 1


# ==========================================
# 7. 게임 결과 계산
# ==========================================

def finish_game():

    player_count = st.session_state.player_count

    scores = []

    for i in range(player_count):

        deck_count = len(st.session_state.decks[i])
        table_count = len(st.session_state.table_piles[i])

        scores.append(deck_count + table_count)

    max_score = max(scores)

    winners = [
        f"{i + 1}번 학생"
        for i, score in enumerate(scores)
        if score == max_score
    ]

    st.session_state.game_over = True
    st.session_state.winner = ", ".join(winners)
    st.session_state.final_scores = scores


# ==========================================
# 8. 카드 뒤집기
# ==========================================

def flip_card(player):

    if st.session_state.game_over:
        return

    if player != st.session_state.turn:
        return

    deck = st.session_state.decks[player]

    if not deck:
        return

    # 카드 한 장을 뒤집어 자신의 더미 위에 놓기
    card = deck.pop(0)

    st.session_state.table_piles[player].append(card)

    st.session_state.message = (
        f"{player + 1}번 학생이 카드를 뒤집었습니다!"
    )

    # 다음 참여자에게 차례 이동
    st.session_state.turn = next_turn(player)

    # 모든 카드가 소진되었을 때
    if all(len(d) == 0 for d in st.session_state.decks):

        # 같은 구성 요소라면 종을 누를 기회를 남김
        if not is_match():
            finish_game()


# ==========================================
# 9. 종 누르기
# ==========================================

def ring_bell(player):

    if st.session_state.game_over:
        return

    if not is_match():

        st.session_state.message = (
            f"아쉽습니다! {player + 1}번 학생, "
            "아직 같은 구성 요소가 아닙니다."
        )

        # 모든 카드가 소진되었다면 게임 종료
        if all(len(d) == 0 for d in st.session_state.decks):
            finish_game()

        return

    # 테이블 위의 모든 카드를 종을 누른 학생이 가져감
    collected = []

    for pile in st.session_state.table_piles:
        collected.extend(pile)

    random.shuffle(collected)

    st.session_state.decks[player].extend(collected)

    collected_count = len(collected)

    # 모든 뒤집은 카드 더미 비우기
    st.session_state.table_piles = [
        [] for _ in range(st.session_state.player_count)
    ]

    # 종을 누른 학생부터 다시 시작
    st.session_state.turn = player

    st.session_state.message = (
        f"🎉 {player + 1}번 학생 성공! "
        f"카드 {collected_count}장을 모두 가져갔습니다!"
    )

    # 게임이 끝났는지 확인
    if all(len(d) == 0 for d in st.session_state.decks):
        finish_game()


# ==========================================
# 10. 화면 디자인
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #FFF9EF;
}

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 900;
    color: #51412F;
    padding: 15px;
}

.sub-title {
    text-align: center;
    font-size: 18px;
    color: #86735C;
    margin-bottom: 25px;
}

.player-box {
    background-color: white;
    border: 3px solid #F0DDBD;
    border-radius: 18px;
    padding: 12px 5px;
    text-align: center;
    min-height: 115px;
}

.card {
    background: linear-gradient(135deg, #FFFFFF, #FFF1D9);
    border: 4px solid #EBCB9B;
    border-radius: 17px;
    min-height: 165px;
    padding: 18px 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    font-size: 20px;
    font-weight: bold;
    color: #453B32;
    margin: 10px 0;
    word-break: keep-all;
    overflow-wrap: break-word;
}

.card-empty {
    background: #F2E8D8;
    border: 3px dashed #D6C4A8;
    color: #A08E76;
    font-size: 38px;
}

.stButton > button {
    border-radius: 12px;
    font-weight: bold;
    min-height: 45px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 11. 제목
# ==========================================

st.markdown(
    '<div class="main-title">🔔 극본 할리갈리 🔔</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    '지문! 대사! 해설! 같은 구성 요소가 모이면 종을 울려라!'
    '</div>',
    unsafe_allow_html=True
)


# ==========================================
# 12. 게임 준비 및 인원 선택
# ==========================================

if "started" not in st.session_state:
    st.session_state.started = False

if not st.session_state.started:

    st.markdown("### 🎮 게임 준비")

    st.info("""
    총 48장의 카드로 게임을 진행합니다.

    구성 요소 카드 12장 + 설명 카드 18장 + 예시 카드 18장

    참여 인원을 선택하면 카드가 자동으로 균등 배분됩니다.
    """)

    player_count = st.selectbox(
        "👧👦 게임 참여 인원",
        options=[2, 3, 4, 5, 6, 7, 8],
        index=2,
        format_func=lambda x: f"{x}명"
    )

    base, remainder = divmod(48, player_count)

    st.write(
        f"1인당 기본 {base}장씩 배분됩니다. "
        f"남는 {remainder}장은 앞 순서 참여자부터 1장씩 더 받습니다."
    )

    if st.button(
        "🎲 카드 섞고 게임 시작!",
        use_container_width=True
    ):

        if not API_KEY or "여기에_" in API_KEY:
            st.error("OpenAI API Key를 먼저 입력해 주세요.")

        else:

            with st.spinner("AI가 극본 카드를 만들고 있습니다..."):

                try:
                    start_game(player_count)
                    st.rerun()

                except Exception as e:
                    st.error(f"게임 준비 오류: {e}")

    st.stop()


# ==========================================
# 13. 게임 상황
# ==========================================

st.markdown("### 📢 게임 상황")

st.info(st.session_state.message)

if not st.session_state.game_over:

    current = st.session_state.turn

    st.markdown(
        f"<h3 style='text-align:center;color:#E65D43;'>"
        f"⭐ {current + 1}번 학생 차례 ⭐</h3>",
        unsafe_allow_html=True
    )


# ==========================================
# 14. 참여자 카드 화면
# ==========================================

st.markdown("### 🃏 참여자별 카드")

player_count = st.session_state.player_count

# 최대 4명씩 한 줄에 배치
for start in range(0, player_count, 4):

    end = min(start + 4, player_count)

    cols = st.columns(end - start)

    for i, col in zip(range(start, end), cols):

        with col:

            is_turn = (
                i == st.session_state.turn
                and not st.session_state.game_over
            )

            remaining = len(st.session_state.decks[i])
            pile = st.session_state.table_piles[i]

            st.markdown(
                f'<div class="player-box">'
                f'<h3>{i + 1}번 학생</h3>'
                f'<p>남은 카드: {remaining}장</p>'
                f'<p>{"⭐ 내 차례!" if is_turn else "차례 기다리는 중"}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

            # 가장 최근에 뒤집은 카드 한 장만 공개
            if pile:

                visible_card = pile[-1]

                content = html.escape(
                    visible_card["content"]
                )

                st.markdown(
                    f'<div class="card">{content}</div>',
                    unsafe_allow_html=True
                )

                st.caption(
                    f"뒤집은 카드: {len(pile)}장"
                )

            else:

                st.markdown(
                    '<div class="card card-empty">🃏</div>',
                    unsafe_allow_html=True
                )

                st.caption("아직 뒤집은 카드가 없습니다.")

            # 카드 뒤집기 버튼
            if st.button(
                "🃏 카드 뒤집기",
                key=f"flip_{i}",
                disabled=(
                    not is_turn
                    or st.session_state.game_over
                    or remaining == 0
                ),
                use_container_width=True
            ):

                flip_card(i)
                st.rerun()

            # 종 버튼
            if st.button(
                "🔔 종 누르기!",
                key=f"bell_{i}",
                disabled=st.session_state.game_over,
                use_container_width=True
            ):

                ring_bell(i)
                st.rerun()


# ==========================================
# 15. 공개된 카드 현황
# ==========================================

st.divider()

st.markdown("### 🔎 현재 공개된 카드")

visible_cards = get_visible_cards()

if visible_cards:

    cols = st.columns(3)

    counts = {
        component: sum(
            1 for item in visible_cards
            if item["card"]["type"] == component
        )
        for component in COMPONENTS
    }

    for i, component in enumerate(COMPONENTS):

        with cols[i]:

            st.metric(
                component,
                f"{counts[component]}장"
            )

else:

    st.write("아직 공개된 카드가 없습니다.")


# ==========================================
# 16. 최종 결과
# ==========================================

if st.session_state.game_over:

    st.balloons()

    st.markdown("## 🏆 게임 종료!")

    st.success(
        f"최종 우승자: {st.session_state.winner}"
    )

    st.markdown("### 최종 카드 보유 수")

    cols = st.columns(4)

    for i, score in enumerate(st.session_state.final_scores):

        with cols[i % 4]:

            st.metric(
                f"{i + 1}번 학생",
                f"{score}장"
            )

    if st.button(
        "🔄 새로운 게임 시작",
        use_container_width=True
    ):

        st.session_state.started = False
        st.rerun()


# ==========================================
# 17. 게임 재시작
# ==========================================

if not st.session_state.game_over:

    st.divider()

    if st.button(
        "🔄 게임 처음부터 다시 시작",
        use_container_width=True
    ):

        st.session_state.started = False
        st.rerun()
