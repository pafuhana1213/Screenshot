# -*- coding: utf-8 -*-
"""
Lyra (x157.github.io) ナレッジノート用インフォグラフィック一括生成。
1600x900 / 暗背景 + Unreal 青 / フラットなテック系。
cover (タイトルカード) と summary (フロー帯 + カードグリッド) を仕様駆動で描画。
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 900
BG       = (24, 25, 29)
PANEL    = (37, 39, 46)
PANEL2   = (46, 49, 58)
STROKE   = (70, 74, 86)
ACCENT   = (59, 142, 234)   # Unreal blue
ACCENT2  = (124, 188, 255)
TEXT     = (233, 236, 241)
SUB      = (173, 180, 193)
CHIPBG   = (38, 52, 78)
CHIPTX   = (171, 205, 255)
GOOD     = (124, 205, 148)
WARN     = (240, 188, 96)
DANGER   = (231, 120, 120)

FONT_CANDIDATES = [
    ("C:/Windows/Fonts/YuGothB.ttc", 0),
    ("C:/Windows/Fonts/YuGothB.ttc", 1),
    ("C:/Windows/Fonts/meiryob.ttc", 0),
    ("C:/Windows/Fonts/YuGothM.ttc", 0),
    ("C:/Windows/Fonts/meiryo.ttc", 0),
    ("C:/Windows/Fonts/msgothic.ttc", 0),
]
FONT_REG = [
    ("C:/Windows/Fonts/YuGothM.ttc", 0),
    ("C:/Windows/Fonts/YuGothR.ttc", 0),
    ("C:/Windows/Fonts/meiryo.ttc", 0),
    ("C:/Windows/Fonts/msgothic.ttc", 0),
]

def _load(cands, size):
    for path, idx in cands:
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    return ImageFont.load_default()

def fb(size):  # bold
    return _load(FONT_CANDIDATES, size)
def fr(size):  # regular
    return _load(FONT_REG, size)

def tlen(draw, s, font):
    return draw.textlength(s, font=font)

def tokenize(s):
    """ASCII の語は塊、CJK は1文字ずつ、空白も単位。"""
    toks, buf = [], ""
    def isascii_word(c):
        return c.isascii() and (c.isalnum() or c in "._:<>+()/=-#&'\"[]")
    for c in s:
        if c == "\n":
            if buf: toks.append(buf); buf=""
            toks.append("\n")
        elif isascii_word(c):
            buf += c
        else:
            if buf: toks.append(buf); buf=""
            toks.append(c)
    if buf: toks.append(buf)
    return toks

def wrap(draw, s, font, max_w):
    lines, cur = [], ""
    for tok in tokenize(s):
        if tok == "\n":
            lines.append(cur); cur=""; continue
        trial = cur + tok
        if tlen(draw, trial, font) <= max_w or cur == "":
            cur = trial
        else:
            lines.append(cur.rstrip()); cur = tok.lstrip(" ")
    if cur: lines.append(cur)
    return lines

def rr(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def draw_header(draw, title, kicker="x157.github.io · Lyra"):
    draw.rectangle([0, 0, W, 8], fill=ACCENT)
    f = fb(46)
    draw.text((60, 40), title, font=f, fill=TEXT)
    fk = fr(22)
    kw = tlen(draw, kicker, fk)
    draw.text((W - 60 - kw, 52), kicker, font=fk, fill=SUB)
    draw.line([60, 118, W - 60, 118], fill=STROKE, width=2)

# ---------------- COVER ----------------
def render_cover(spec, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # bg accent shapes
    d.rectangle([0, 0, 14, H], fill=ACCENT)
    d.rectangle([0, H-14, W, H], fill=(31,33,39))
    # kicker
    fk = fb(28)
    d.text((90, 120), spec.get("kicker", "LYRA STARTER GAME"), font=fk, fill=ACCENT2)
    # title (jp, large, possibly multi-line)
    ft = fb(72)
    lines = wrap(d, spec["title"], ft, W - 200)
    y = 190
    for ln in lines:
        d.text((90, y), ln, font=ft, fill=TEXT)
        y += 92
    # subtitle (english)
    fs = fr(34)
    sub_lines = wrap(d, spec.get("subtitle",""), fs, W - 220)
    y += 6
    for ln in sub_lines:
        d.text((92, y), ln, font=fs, fill=SUB)
        y += 46
    # chips
    chips = spec.get("chips", [])
    fc = fb(24)
    cx, cy = 92, max(y + 28, H - 240)
    for ch in chips:
        cw = tlen(d, ch, fc)
        bw = cw + 40
        if cx + bw > W - 90:
            cx = 92; cy += 64
        rr(d, [cx, cy, cx + bw, cy + 48], 12, fill=CHIPBG, outline=(60,90,140), width=1)
        d.text((cx + 20, cy + 9), ch, font=fc, fill=CHIPTX)
        cx += bw + 16
    # footer
    ff = fr(22)
    d.text((92, H - 56), spec.get("footer","UE / ゲーム開発ナレッジ — Lyra 技術記事まとめ (XistGG dev-notes)"),
           font=ff, fill=SUB)
    img.save(out)
    print("WROTE", out)

# ---------------- SUMMARY ----------------
def draw_flow(d, y, steps, accent=ACCENT):
    """横並びのフロー帯。steps: ラベル文字列のリスト。"""
    n = len(steps)
    left, right = 60, W - 60
    arrow = 30
    total_arrow = arrow * (n - 1)
    bw = (right - left - total_arrow) / n
    bh = 86
    fsz = 25
    # shrink font until labels fit
    f = fb(fsz)
    tmp = Image.new("RGB",(10,10)); td = ImageDraw.Draw(tmp)
    while fsz > 14:
        f = fb(fsz)
        ok = all(max(tlen(td, l, f) for l in wrap(td, s, f, bw-24)) <= bw-24 for s in steps)
        if ok: break
        fsz -= 1
    x = left
    for i, s in enumerate(steps):
        rr(d, [x, y, x + bw, y + bh], 12, fill=PANEL2, outline=accent, width=2)
        lines = wrap(d, s, f, bw - 24)
        ly = y + (bh - len(lines)*(fsz+4))/2
        for ln in lines:
            lw = tlen(d, ln, f)
            d.text((x + (bw-lw)/2, ly), ln, font=f, fill=TEXT)
            ly += fsz + 4
        if i < n - 1:
            ax = x + bw + arrow/2
            d.text((x + bw + 4, y + bh/2 - 18), "→", font=fb(34), fill=accent)
        x += bw + arrow
    return y + bh

def draw_cards(d, y_top, cards):
    cols = 2
    left, right = 60, W - 60
    gap = 26
    cw = (right - left - gap) / cols
    rows = (len(cards) + cols - 1) // cols
    avail = (H - 70) - y_top
    ch = (avail - gap * (rows - 1)) / rows
    fh = fb(26)
    fbl = fr(21)
    for i, c in enumerate(cards):
        r, cidx = divmod(i, cols)
        x = left + cidx * (cw + gap)
        y = y_top + r * (ch + gap)
        col = c.get("color", ACCENT)
        rr(d, [x, y, x + cw, y + ch], 14, fill=PANEL, outline=STROKE, width=1)
        d.rectangle([x, y+14, x+6, y+ch-14], fill=col)
        # heading
        hx = x + 24
        hlines = wrap(d, c["h"], fh, cw - 44)
        hy = y + 16
        for hl in hlines:
            d.text((hx, hy), hl, font=fh, fill=ACCENT2)
            hy += 32
        # bullets
        by = hy + 6
        for b in c.get("b", []):
            blines = wrap(d, "▸ " + b, fbl, cw - 48)
            for j, bl in enumerate(blines):
                if by > y + ch - 26:
                    break
                d.text((hx + (0 if j == 0 else 18), by), bl, font=fbl, fill=TEXT if j==0 else SUB)
                by += 27
            by += 4

def render_summary(spec, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    draw_header(d, spec["title"], spec.get("kicker","x157.github.io · Lyra"))
    y = 140
    if spec.get("flow"):
        flabel = spec.get("flow_label")
        if flabel:
            d.text((60, y), flabel, font=fb(22), fill=SUB); y += 32
        y = draw_flow(d, y, spec["flow"], spec.get("flow_accent", ACCENT))
        y += 24
    draw_cards(d, y, spec["cards"])
    img.save(out)
    print("WROTE", out)


# ======================= SPECS =======================
COVERS = {
 "lyra-overview-setup": {
   "kicker":"LYRA STARTER GAME — OVERVIEW",
   "title":"Lyra 全体像・導入・運用",
   "subtitle":"Build Your Game on Lyra — Setup, 3-Branch Upgrade & Operation",
   "chips":["Lyra = engine code","GameFeature Plugin","LYRAGAME_API","lyra-main / lyra-xist / xist-game","ResavePackages","CommonUI 強制"],
 },
 "lyra-experience-flow": {
   "kicker":"EXPERIENCE & GAME FLOW",
   "title":"Lyra Experience と\n初期化・ゲームフェーズ",
   "subtitle":"Experience System, Game Init & Game Phase Subsystem",
   "chips":["ULyraExperienceDefinition","ExperienceManagerComponent","OnExperienceLoaded","ULyraPawnData","GamePhaseSubsystem"],
 },
 "lyra-gamefeatures-modular": {
   "kicker":"GAMEFEATURE & MODULAR GAMEPLAY",
   "title":"Game Feature Plugins と\nModular Gameplay",
   "subtitle":"Runtime Feature Injection in Lyra",
   "chips":["UGameFeatureData","AddComponents / AddAbilities","Installed→Registered→Loaded→Active","GameFrameworkComponentManager","ModularCharacter"],
 },
 "lyra-input-enhanced": {
   "kicker":"INPUT — ENHANCED INPUT",
   "title":"Lyra の入力\n(Enhanced Input)",
   "subtitle":"Routing Keys → GameplayTag → GameplayAbility",
   "chips":["InputMappingContext","UInputAction","ULyraInputConfig","InputTag.*","BindAbilityActions","CommonUI ActionRouter"],
 },
 "lyra-ui-commonui": {
   "kicker":"UI — COMMON UI + UI EXTENSION",
   "title":"Lyra の UI\n(Common UI + UI Extension)",
   "subtitle":"Layered HUD & Front-End via GameplayTag",
   "chips":["UCommonActivatableWidget","UPrimaryGameLayout","UI.Layer.Game/Menu/Modal","UIExtensionSubsystem","HUD.Slot.*"],
 },
 "lyra-gas": {
   "kicker":"GAMEPLAY ABILITY SYSTEM",
   "title":"Lyra の GAS\n(Gameplay Ability System)",
   "subtitle":"Abilities, Net Policies & Client→Server TargetData",
   "chips":["ULyraGameplayAbility","LocalPredicted","ULyraAbilitySet","FScopedPredictionWindow","EndAbility 自己責任"],
 },
 "lyra-character-equipment": {
   "kicker":"CHARACTER / EQUIPMENT / WEAPON / INVENTORY",
   "title":"Lyra のキャラ・装備・\n武器・インベントリ",
   "subtitle":"Character Parts & the Inventory→Equipment→Weapon Stack",
   "chips":["ULyraInventoryItemDefinition","EquippableItem Fragment","ULyraEquipmentDefinition","ULyraWeaponInstance","QuickBar","CharacterParts"],
 },
 "lyra-combat-teams": {
   "kicker":"HEALTH & DAMAGE / INTERACTION / TEAMS",
   "title":"Lyra の体力&ダメージ・\nインタラクション・チーム",
   "subtitle":"Health & Damage / Interaction / Team Systems",
   "chips":["ULyraHealthSet","ULyraDamageExecution","GA_Interact","ULyraTeamSubsystem","GameplayCue"],
 },
 "lyra-gamemodes-online": {
   "kicker":"GAME MODES & ONLINE",
   "title":"Lyra のゲームモード・\nマップ & Online",
   "subtitle":"ShooterCore / ShooterMaps GFP & OnlineServices (EOS)",
   "chips":["ShooterCore GFP","B_ShooterGame_Elimination","Control Points","OnlineServices (OSSv2)","CommonSession / EOS"],
 },
}

SUMMARIES = {
 "lyra-overview-setup": {
   "title":"Lyra 全体像・導入・運用 — 要点",
   "cards":[
     {"h":"「Lyra は engine code」原則","b":[
        "base Lyra は改変しない。名前空間は予約済み",
        "全カスタムは GFP + 専用 C++ プラグイン (XCL/XaiLife) に隔離。最低 1 GFP を作る"]},
     {"h":"拡張 > 複製 / ただしバイナリは複製","b":[
        "C++ は LYRAGAME_API エクスポートで extend",
        "uasset (BP/DataAsset/Widget) はマージ不可 → 複製して GFP 内で編集"]},
     {"h":"3 ブランチ更新戦略","color":GOOD,"b":[
        "lyra-main (無改変の素 Lyra) → lyra-xist (最小 hack) → xist-game (本番)",
        "Lyra C++ 改変は直接 lyra-xist へコミットしマージで降ろす"]},
     {"h":"採否トレードオフ","b":[
        "Pros: GAS / Enhanced Input / ModularGameplay / 4 ネット構成が即入手",
        "Cons: CommonUI 入力強制・GAS 学習コスト。不要ならオーバースペック"]},
     {"h":"5.1 はアセット再保存が必須","color":WARN,"b":[
        "DDC バグ回避に -run=ResavePackages コマンドレット (要 Perforce 接続)",
        "再起動 2 回で起動高速化を確認"]},
     {"h":"Lyra が用意しないもの","color":DANGER,"b":[
        "実用 Pawn・汎用 AI Controller・Ability 付き Actor は未提供",
        "Equipment/Inventory/Weapon は prototype → 複製して足場に"]},
   ],
 },
 "lyra-experience-flow": {
   "title":"Lyra Experience & 初期化・ゲームフェーズ — 要点",
   "flow_label":"ゲーム起動フロー (BeginPlay では始めない)",
   "flow":["マップロード\n+WorldSettings の\nDefault Experience","InitGame /\nInitGameState","BeginPlay\n(ランダム順)","ExperienceMgr が\nGFP 非同期ロード→Active","PawnData 適用\nで Pawn 生成","OnExperienceLoaded\nブロードキャスト"],
   "cards":[
     {"h":"Experience = データ駆動のゲーム定義","b":[
        "ULyraExperienceDefinition が PawnData・GameFeatureActions・ActionSets を宣言",
        "レベルは容器。中身は Experience が決める。WorldSettings が既定 Experience を持つ"]},
     {"h":"ロードの 4 ステート","color":GOOD,"b":[
        "StartExperienceLoad: Loading → LoadingGameFeatures → ExecutingActions → Loaded",
        "ULyraExperienceManagerComponent (GameState 上) が司る"]},
     {"h":"BeginPlay 禁止・OnExperienceLoaded を待て","color":DANGER,"b":[
        "GFP/PawnData は BeginPlay 時点で未確定。はるか後に Loaded",
        "CallOrRegister_OnExperienceLoaded / High・Normal・Low 優先度で登録"]},
     {"h":"GamePhase = GameplayTag 階層","b":[
        "ULyraGamePhaseSubsystem + ULyraGamePhaseAbility (OnBeginPhase/OnEndPhase)",
        "親子は共存可・兄弟は共存不可 (例: Game.Playing と Game.ShowingScore)"]},
     {"h":"デバッグ","b":[
        "lyra.chaos.ExperienceDelayLoad.* で遅延注入し BeginPlay 依存を炙り出す",
        "ModularGameplay.DumpGameFrameworkComponentManagers で注入確認"]},
   ],
 },
 "lyra-gamefeatures-modular": {
   "title":"Game Feature Plugins & Modular Gameplay — 要点",
   "flow_label":"GFP ライフサイクル状態遷移 (Active で初めて Action 実行)",
   "flow":["Installed\n存在認識","Registered\n.uplugin+\nGameFeatureData 登録","Loaded\nメモリロード\n(Action 未実行)","Active\nGameFeatureActions\n実行"],
   "flow_accent":GOOD,
   "cards":[
     {"h":"GFP は base game code に触れる","b":[
        "通常 Plugin は base code に CANNOT access、GFP は CAN access (MOD 的)",
        "Lyra では Experience がマップ連動で対象 GFP を Active まで遷移させる"]},
     {"h":"GameFeatureActions で動的注入","b":[
        "AddComponents / AddAbilities / AddInputContextMapping / AddWidgets",
        "UGameFeatureData がこれらのリストを保持。Deactivate で注入物を剥がす"]},
     {"h":"Modular Gameplay = 注入の基盤","b":[
        "UGameFrameworkComponentManager (GameInstance Subsystem) が統括",
        "ALyraCharacter/PlayerController/PlayerState は Modular* 系を継承"]},
     {"h":"注入が効かない最頻原因","color":DANGER,"b":[
        "対象が Modular* ベース未継承で受信登録されていない",
        "AddComponents は『受信側がレシーバ登録済み』が前提"]},
     {"h":"Runtime サフィックス除去","color":WARN,"b":[
        "C++ GFP のモジュール名 XistGameRuntime → XistGame に揃える手順",
        ".uasset には効かない → アセット追加前に実施"]},
     {"h":"デバッグ","b":[
        "Log LogGameFeatures Verbose / Log LogModularGameplay Verbose",
        "ModularGameplay.DumpGameFrameworkComponentManagers"]},
   ],
 },
 "lyra-input-enhanced": {
   "title":"Lyra の入力 (Enhanced Input) — 要点",
   "flow_label":"入力 → アビリティ発火のチェーン",
   "flow":["物理キー\n(Space)","IMC\nIA_Jump にマップ","UInputAction","GameplayTag\nInputTag.Jump","BindAbilityActions\n→ ASC","GameplayAbility\n発火"],
   "cards":[
     {"h":"「キーではなくアクション」","b":[
        "UInputMappingContext (IMC) が priority 付きで着脱、消費で下位を遮断",
        "Triggers(押下/長押し/Chord) と Modifiers(デッドゾーン等) で柔軟化"]},
     {"h":"ULyraInputConfig が接着剤","color":GOOD,"b":[
        "NativeInputActions → 直接 C++ 関数 (Move/Look)",
        "AbilityInputActions → InputTag 経由で GameplayAbility 発火"]},
     {"h":"ルーティングの実体","b":[
        "ULyraInputComponent::BindAbilityActions / BindNativeAction",
        "Input_AbilityInputTagPressed → ASC->AbilityInputTagPressed(Tag)"]},
     {"h":"動的着脱は Game Feature Action","b":[
        "AddInputContextMapping(IMC) / AddInputBinding / AddInputConfig",
        "プラグイン単位で入力セットを差し替え"]},
     {"h":"入力モードは CommonUI 経由","color":DANGER,"b":[
        "旧 SetInputMode は効かない → SetActiveUIInputConfig(FUIInputConfig)",
        "Game(不可視)/All(可視・Game可)/Menu(可視・Game不可)。NoCapture 禁止"]},
   ],
 },
 "lyra-ui-commonui": {
   "title":"Lyra の UI (Common UI + UI Extension) — 要点",
   "flow_label":"UPrimaryGameLayout の 4 レイヤースタック (入力は最上位の可視レイヤーへ)",
   "flow":["UI.Layer.Game\nHUD","UI.Layer.GameMenu\n(未使用・空き)","UI.Layer.Menu\n設定/メニュー","UI.Layer.Modal\nダイアログ"],
   "cards":[
     {"h":"Activatable Widget が基底","b":[
        "UCommonActivatableWidget → ULyraActivatableWidget → ULyraHUDLayout",
        "ActionRouter が Input Mode を管理。入力はトップの可視層のみ消費"]},
     {"h":"HUD 組み立てフロー","color":GOOD,"b":[
        "Experience → Action Set → W_ShooterHUDLayout を UI.Layer.Game に割当",
        "Escape 押下で EscapeMenuClass を UI.Layer.Menu に push"]},
     {"h":"UI Extension = 疎結合スロット","b":[
        "UIExtensionPointWidget [Tag: HUD.Slot.Score] を HUD に置く",
        "GFP が UUIExtensionSubsystem に『このタグへこの Widget』を登録/解除"]},
     {"h":"フロントエンドのカスタマイズ","b":[
        "Asset Manager に Map/LyraLobbyBackground のスキャン先を追加 → 要エディタ再起動",
        "B_LyraFrontEnd_Experience とロビー背景を複製して差し替え"]},
     {"h":"つまずき","color":DANGER,"b":[
        "Extension Point は GameplayTag のタイポで無言で出ない",
        "Modal は直接 push せず UI Messaging Subsystem 経由。CommonUI.DumpActivatableTree で確認"]},
   ],
 },
 "lyra-gas": {
   "title":"Lyra の GAS — 要点",
   "flow_label":"アビリティのライフサイクル (EndAbility は自己責任で明示呼び出し)",
   "flow":["OnGiveAbility","CanActivateAbility\n通過","ActivateAbility\n(何度でも)","EndAbility\n※明示必須","OnRemoveAbility"],
   "cards":[
     {"h":"ネット実行ポリシー 4 種","color":GOOD,"b":[
        "LocalPredicted(既定/両側/要RPC)・LocalOnly(C のみ/UI)",
        "ServerOnly(S のみ/結果レプリ)・ServerInitiated(S 起点/両側)"]},
     {"h":"Lyra の入力→発火 3 層","b":[
        "InputAction → IMC → ULyraInputConfig → InputTag → ULyraAbilitySet",
        "アビリティは AbilitySet 経由で付与、InputTag で起動"]},
     {"h":"新規アビリティ作成 6 手順","b":[
        "IA 作成 → InputTag → IMC 割当 → InputConfig 紐付け",
        "→ ULyraGameplayAbility(BP) → ULyraAbilitySet に登録 (コード不要)"]},
     {"h":"Client→Server TargetData","b":[
        "new TargetData → NotifyTargetDataReady → CommitAbility",
        "FScopedPredictionWindow → CallServerSetReplicatedTargetData (RPC) → Consume"]},
     {"h":"EndAbility × scope-lock の安全弁","color":WARN,"b":[
        "ScopeLockCount==0 のときだけ EndAbilityCleanup → Super::EndAbility",
        "TargetData はヒープ確保必須。予測キーを送受で一致させる"]},
     {"h":"XCLGameplayAbility (著者派生)","b":[
        "ActivateLocalPlayerAbility / ActivateServerAbility に二分",
        "Listen Server は両方実行 → 二重処理に注意"]},
   ],
 },
 "lyra-character-equipment": {
   "title":"Lyra のキャラ・装備・武器・インベントリ — 要点",
   "flow_label":"3 層継承スタック (Inventory が基盤 → Equipment → Weapon)",
   "flow":["InventoryItem\n(EquippableItem\nFragment)","EquipmentDefinition","EquipmentInstance","WeaponInstance","RangedWeaponInstance"],
   "cards":[
     {"h":"Inventory (最下層・フラグメント方式)","color":WARN,"b":[
        "ULyraInventoryItemDefinition + ItemInstance、Fragment で機能拡張",
        "5.0.3 はスタック壊れた prototype。5.1 で sub-object レプリ化"]},
     {"h":"Equipment (中間層・武器の基盤)","b":[
        "EquipmentDefinition=定数(Instance型/AbilitySets/Actors)、Instance=実体",
        "EquipmentManagerComponent.EquipItem + QuickBarComponent が事実上必須"]},
     {"h":"Weapon (最上層・GAS 戦闘)","color":GOOD,"b":[
        "ULyraWeaponInstance ⊂ RangedWeaponInstance、WeaponStateComponent がヒット管理",
        "GA_RangedWeapon: PerformLocalTargeting → RPC → サーバーで GE+GameplayCue"]},
     {"h":"Character Parts (純コスメ合成)","b":[
        "Controller Component(server/決定) vs Pawn Component(client/実スポーン)",
        "サーバーは不可視メッシュ。Cosmetic.AnimationStyle.* タグでアニメ分岐"]},
     {"h":"Unarmed アニメバグ (Quinn/Feminine)","color":DANGER,"b":[
        "Link(青/masculine固定) → Relink Anim Class Layers(紫)",
        "Cosmetic.AnimationStyle.Feminine で _Feminine レイヤーを Select 分岐"]},
     {"h":"近接武器の落とし穴","b":[
        "GA_Melee が FromEquipment 非継承 → 装備別ダメージ/射程を読めない",
        "Katana 等を作るなら FromEquipment 派生に作り直す"]},
   ],
 },
 "lyra-combat-teams": {
   "title":"Lyra の体力&ダメージ・インタラクション・チーム — 要点",
   "flow_label":"ダメージ適用→死亡フロー (GAS 標準)",
   "flow":["GE で Damage 属性+","DamageExecution\nが Health−(最小0)","Health==0\nOnOutOfHealth","GameplayEvent.Death\n+Elimination.Message","HealthComponent\nOnDeathStarted"],
   "flow_accent":DANGER,
   "cards":[
     {"h":"ヘルスの前提条件","color":DANGER,"b":[
        "ダメージ/回復を受ける actor は ASC + ULyraHealthSet が必須",
        "ULyraCombatSet が攻撃側の base damage/healing。ALyraCharacter は内蔵"]},
     {"h":"Damage/Healing は meta-attribute","b":[
        "Health を直接書かず Damage/Healing を GE で立て Execution に処理させる",
        "ULyraDamageExecution / ULyraHealExecution。GE_Damage_Basic_Instant 等"]},
     {"h":"Interaction = 付与 + 発動の 2 段","color":GOOD,"b":[
        "GrantNearbyInteraction が球トレース(500cm/0.1s)→PlayerState に Ability 付与",
        "視線 + IA_Interact(200cm) で GA_Interaction_Collect 発動"]},
     {"h":"Interaction の前提","b":[
        "IInteractableTarget 実装 + Lyra_TraceChannel_Interaction オーバーラップ",
        "公式 Doc の InteractionScanRate は typo、正しくは InteractionScanRange"]},
     {"h":"Team = GameState 複製で管理","b":[
        "ULyraTeamSubsystem / TeamCreationComponent / TeamDisplayAsset(色)",
        "ChangeTeamForActor は PlayerState に対して呼ぶ。既定 FF 無効"]},
     {"h":"プロトタイプ注意","color":WARN,"b":[
        "Health/Damage と Team は production 品質",
        "Interaction 上の Inventory は PROTO → 拡張せず自作する"]},
   ],
 },
 "lyra-gamemodes-online": {
   "title":"Lyra のゲームモード・マップ & Online — 要点",
   "flow_label":"マップ → Experience → 依存 GFP 有効化の連鎖",
   "flow":["L_Convolution_Blockout\n(マップ)","B_LyraShooterGame_\nControlPoints\n(Experience)","ShooterCore GFP\nを明示 Activate","PawnData/AbilitySet/\nComponent/Widget 注入"],
   "cards":[
     {"h":"ShooterCore = シューターの土台 GFP","color":GOOD,"b":[
        "Experience B_ShooterGame_Elimination、Pawn B_Hero_ShooterMannequin",
        "GAS 9種(Jump/Dash/ADS/Grenade/Melee...)・QuickBar 3 スロット・HUD 拡張"]},
     {"h":"ShooterMaps = ShooterCore の実装例","b":[
        "L_Expanse(エリミ)・L_Convolution(Control Point)・L_FiringRange(射撃場)",
        "Control Point は ShooterCore を明示有効化しないと休眠のまま"]},
     {"h":"モードはマップに直書きしない","b":[
        "マップ→Experience 関連付け→GFP/PawnData/AbilitySet/Component/Widget 注入",
        "B_ControlPoint_Scoring 等を LyraGameState に注入"]},
     {"h":"OSSv2 vs OSSv1","color":WARN,"b":[
        "OnlineServices(OSSv2)=UE5.1+/5.5 beta/Epic 推奨、OSS(v1)=legacy",
        "Common User + Common Session で実演。5.5 はデフォルトでは動かない"]},
     {"h":"EOS 設定が肝","color":DANGER,"b":[
        "Config/Custom/EOS/DefaultEngine.ini に Product/Sandbox/Deployment/Client",
        "GetLobbiesInterface()==nullptr は EOS 設定ミスの赤フラグ。先頭 + を削除"]},
     {"h":"セッションフロー","b":[
        "ログイン/EOS 初期化 → ホストが Lobby 作成 → 検索 → Join",
        "具体 API は Epic 公式 Common User Plugin が一次情報"]},
   ],
 },
}

def main():
    sel = sys.argv[1:] if len(sys.argv) > 1 else list(COVERS.keys())
    for slug in sel:
        render_cover(COVERS[slug], f"NotionKB_{slug}-cover.png")
        render_summary(SUMMARIES[slug], f"NotionKB_{slug}-summary.png")

if __name__ == "__main__":
    main()
