#!/usr/bin/env python3
"""Patch the original uploaded Godot ZIP at build time, without re-upload."""
from pathlib import Path
ROOT = Path("game")

def rewrite(rel, transform):
    path = ROOT / rel
    old = path.read_text(encoding="utf-8")
    new = transform(old)
    if new == old:
        raise RuntimeError("No patch applied to " + rel)
    path.write_text(new, encoding="utf-8")
    print("Patched:", rel, "bytes:", len(new))

def exact(text, before, after, where):
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"{where}: expected one occurrence; found {count}: {before[:100]!r}")
    return text.replace(before, after, 1)

def japanese_hud(s):
    s = exact(s, "var ui_scale: float = 1.0",
              "var ui_scale: float = 1.0\nvar mouse_stick: bool = false\nvar stick_area: Control\nvar version_text: Label",
              "hud fields")
    s = exact(s, "    _build_ui()\n    resized.connect(_layout)",
              "    _build_ui()\n    set_process_input(true)\n    resized.connect(_layout)",
              "enable raw input")
    s = exact(s, '_label("✦ ASTRA LEGENDS", 19, Color("f4d59a"), panel).position = Vector2(17, 12)',
              '_label("✦ ASTRA LEGENDS", 19, Color("f4d59a"), panel).position = Vector2(17, 12)\n    version_text = _label("日本語版 v11.2", 13, Color("ffdf94"))',
              "version label")
    labels = {
        '["ATK", "attack"':'["攻撃", "attack"',
        '["SPELL", "magic"':'["魔法", "magic"',
        '["SKILL", "skill"':'["特技", "skill"',
        '["DODGE", "dodge"':'["回避", "dodge"',
        '["JUMP", "jump"':'["ジャンプ", "jump"',
        '["TALK", "interact"':'["話す", "interact"',
        '["MENU", "menu"':'["メニュー", "menu"',
    }
    for before, after in labels.items():
        s = exact(s,before,after,"button label")
    s = exact(s, 'close.text = "Continue  ›"', 'close.text = "つづける  ›"', "dialogue button")
    s = exact(s, '_label("ADVENTURER\'S MENU", 22', '_label("冒険メニュー", 22', "menu title")
    s = exact(s, 'var options: Array = ["POTION", "UPGRADE", "ARMOR", "SAVE", "HERO"]',
              'var options: Array = [["回復薬", "potion"], ["剣の強化", "upgrade"], ["防具の強化", "armor"], ["セーブ", "save"], ["主人公変更", "hero"]]',
              "menu labels and action IDs")
    s = exact(s, 'btn.text = str(options[i])','btn.text = str(options[i][0])',"menu button text")
    s = exact(s, 'var action: String = str(options[i]).to_lower()','var action: String = str(options[i][1])',"menu actions")
    s = exact(s, 'exit.text = "CLOSE"', 'exit.text = "閉じる"', "menu close")
    s = exact(s, '    menu_back.hide()\n\nfunc _layout()',
              '''    menu_back.hide()
    # A dedicated, invisible touch area also receives emulated mouse clicks
    # on mobile browsers that do not forward native screen touches to Godot.
    stick_area = Control.new()
    stick_area.name = "VirtualStickTouchArea"
    stick_area.mouse_filter = Control.MOUSE_FILTER_STOP
    add_child(stick_area)
    stick_area.gui_input.connect(_stick_gui_input)

func _layout()''', "capture zone")
    s = exact(s,'    panel.position = Vector2(18, 17)',
              '''    version_text.position = Vector2(18, 141)
    stick_area.position = Vector2(0, h * 0.40)
    stick_area.size = Vector2(w * 0.44, h * 0.60)
    panel.position = Vector2(18, 17)''',"touch area layout")
    start = s.index("func _input(event: InputEvent) -> void:")
    stop  = s.index("func _set_axis(touch: Vector2) -> void:", start)
    new_input = '''func _can_start_stick(p: Vector2) -> bool:
    return p.x >= 0.0 and p.x < size.x * 0.45 and p.y > size.y * 0.40 and not _point_is_button(p)

func _begin_stick(p: Vector2, pointer_id: int) -> void:
    if stick_id != -1 or not _can_start_stick(p) or dialog_back.visible or menu_back.visible:
        return
    stick_id = pointer_id
    stick_center = Vector2(clampf(p.x, 72.0, size.x * 0.42), clampf(p.y, size.y * 0.56, size.y - 70.0))
    _set_axis(p)

func _release_stick() -> void:
    stick_id = -1
    mouse_stick = false
    axis = Vector2.ZERO
    stick_moved.emit(axis)
    queue_redraw()

func _mouse_pointer(p: Vector2, pressed: bool) -> void:
    if pressed:
        if stick_id == -1 and _can_start_stick(p):
            mouse_stick = true
            _begin_stick(p, 999)
    elif mouse_stick:
        _release_stick()

func _stick_gui_input(event: InputEvent) -> void:
    # Control-local positions are converted to viewport coordinates.
    if event is InputEventScreenTouch:
        var touch: InputEventScreenTouch = event
        var p: Vector2 = stick_area.position + touch.position
        if touch.pressed:
            if stick_id == -1:
                _begin_stick(p, touch.index)
        elif stick_id == touch.index:
            _release_stick()
    elif event is InputEventScreenDrag:
        var drag: InputEventScreenDrag = event
        if drag.index == stick_id:
            _set_axis(stick_area.position + drag.position)
    elif event is InputEventMouseButton:
        var click: InputEventMouseButton = event
        if click.button_index == MOUSE_BUTTON_LEFT:
            _mouse_pointer(stick_area.position + click.position, click.pressed)
    elif event is InputEventMouseMotion and mouse_stick:
        _set_axis(stick_area.position + (event as InputEventMouseMotion).position)

func _input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        var touch: InputEventScreenTouch = event
        if touch.pressed:
            if stick_id == -1:
                _begin_stick(touch.position, touch.index)
            elif touch.position.x > size.x * 0.44 and look_id == -1 and not _point_is_button(touch.position):
                look_id = touch.index
        else:
            if touch.index == stick_id:
                _release_stick()
            if touch.index == look_id:
                look_id = -1
    elif event is InputEventScreenDrag:
        var drag: InputEventScreenDrag = event
        if drag.index == stick_id:
            _set_axis(drag.position)
        elif drag.index == look_id:
            camera_swiped.emit(drag.relative)
    elif event is InputEventMouseButton:
        var click: InputEventMouseButton = event
        if click.button_index == MOUSE_BUTTON_LEFT:
            _mouse_pointer(click.position, click.pressed)
    elif event is InputEventMouseMotion:
        var mouse_event: InputEventMouseMotion = event
        if mouse_stick:
            _set_axis(mouse_event.position)
        elif Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
            camera_swiped.emit(mouse_event.relative)

'''
    s = s[:start] + new_input + s[stop:]
    s = exact(s, 'var quests: Array[String] = ["Chapter I — The Fallen Star", "The Wolves of Silverwood", "The Relic Beneath the Ruins", "The Guardian of Dawn", "Return to the Elder", "Chapter I Complete"]',
              'var quests: Array[String] = ["第1章 ― 墜ちた星", "シルバーウッドの狼", "遺跡に眠る星の秘宝", "暁の守護者", "長老のもとへ戻る", "第1章 クリア"]',
              "quest titles")
    s = exact(s, 'var hints: Array[String] = ["Speak to Elder Elian in the village", "Defeat 3 forest wolves", "Find the luminous chest in the ruins", "Defeat the guardian at the altar", "Return to Elder Elian for your reward", "Explore freely · more chapters planned"]',
              'var hints: Array[String] = ["村で長老エリアンに話しかけよう", "森の狼を3体倒そう", "北の遺跡にある光る宝箱を探そう", "祭壇の守護者を倒そう", "長老エリアンのもとへ報告しよう", "自由に探索しよう（続きは開発中）"]',
              "quest objectives")
    s = exact(s, 'coin_text.text = "Lv.%d   XP %d/%d     %d G"',
              'coin_text.text = "Lv.%d   経験値 %d/%d   %d G"', "status XP")
    return s

def japanese_story(s):
    pairs=[
      ("Swift evasion!", "華麗に回避した！"),
      ("The fallen star awaits. Speak to Elder Elian.", "墜ちた星の謎を追え。まずは長老エリアンに話そう。"),
      ("You awaken at Silverwood village.", "シルバーウッドの村で目を覚ました。"),
      ("Your journey is not over...", "旅はまだ終わらない……"),
      ("Dodged!", "攻撃を回避した！"),
      ("The guardian has awakened at the ruins!", "遺跡で守護者が目覚めた！"),
      ("The forest is safer. Find the star relic!", "森に平和が戻った。星の秘宝を探そう！"),
      ("Guardian defeated! Return to Elder Elian.", "守護者を倒した！ 長老エリアンに報告しよう。"),
      ("Arc Slash", "円月斬り"),
      ("Hit", "命中"),
      ("damage", "ダメージ"),
      ("Recovered HP", "HPを回復した！"),
      ("No potion / already healthy", "回復薬がないか、HPが満タンです"),
      ("Sword upgraded!", "剣を強化した！"),
      ("Armor reinforced!", "防具を強化した！"),
      ("Need %d gold", "ゴールドが%d足りません"),
      ("Adventure saved", "セーブ完了"),
      ("Save failed", "セーブ失敗"),
      ("Action unavailable / not enough MP", "今は使えないかMP不足です"),
      ("Moonflower harvested. +1 potion", "月花を採取！ 回復薬＋1"),
      ("Nothing to interact with nearby", "近くに調べられるものはありません"),
      ("Elder Elian: The dawn-star has shattered! Three wild wolves guard the path. Defeat them, and seek the ancient relic.", "長老エリアン：暁の星が砕けてしまった！ 森の狼を3体倒し、古代の秘宝を探してほしい。"),
      ("Elder Elian: The path cannot be crossed until three wolves are driven away.", "長老エリアン：3体の狼を追い払わなければ先へは進めぬ。"),
      ("Elder Elian: The forgotten relic awaits in a chest at the northern ruins.", "長老エリアン：北の遺跡の宝箱に忘れられた秘宝が眠っておる。"),
      ("Elder Elian: The Guardian of Dawn must be overcome. Stay brave.", "長老エリアン：暁の守護者を打ち倒すのじゃ。勇気を忘れるな。"),
      ("Elder Elian: The star shines again! Our kingdom owes you its future. [Quest complete: +180 G, +170 XP]", "長老エリアン：星の輝きが戻った！ 王国は救われたぞ。［報酬：180G・経験値170］"),
      ("Elder Elian: The road beyond Silverwood is only beginning. More chapters are still in development.", "長老エリアン：シルバーウッドの先にも冒険は続く。続きは開発中じゃ。"),
      ("Rowan: Your blade needs strengthening. Open MENU to upgrade your sword and armor using gold.", "鍛冶師ローワン：剣と防具を強化するなら、メニューでゴールドを使いな。"),
      ("Mira: A healing potion for 20 gold. Safe travels, adventurer!", "商人ミラ：回復薬を20Gでどうぞ。旅の無事を祈ってるよ。"),
      ("Mira: I sell healing potions for 20 gold. Come back once you've earned enough.", "商人ミラ：回復薬は20Gだよ。お金が貯まったらおいで。"),
      ("Star relic acquired! The ancient guardian awakens.", "星の秘宝を入手！ 古き守護者が目覚める。"),
      ("Treasure! +60 gold and +1 potion", "宝箱を発見！ 60Gと回復薬を入手。"),
      ("Saved", "セーブしました")
    ]
    for original, japanese in pairs:
        s = exact(s, '"'+original+'"','"'+japanese+'"', "story translation")
    s = exact(s, '_message("Hero: " + next_id.capitalize())',
              '_message("主人公を変更：" + ("アスター" if next_id == "aster" else "リラ"))',
              "hero name")
    return s

def touch_smoke(s):
    needle = '    var data: Node = root.get_node_or_null("GameData")'
    extra = '''    if hud != null and hero != null:
        var center: Vector2 = hud.get("stick_center")
        var tap: InputEventScreenTouch = InputEventScreenTouch.new()
        tap.index = 7
        tap.pressed = true
        tap.position = center
        hud._input(tap)
        var move: InputEventScreenDrag = InputEventScreenDrag.new()
        move.index = 7
        move.position = center + Vector2(0.0, -52.0)
        move.relative = Vector2(0.0, -52.0)
        hud._input(move)
        var mobile_axis: Vector2 = hero.get("input_axis")
        _require(mobile_axis.y < -0.5, "iPhone joystick drag emits screen-forward axis")
        var end: InputEventScreenTouch = InputEventScreenTouch.new()
        end.index = 7
        end.pressed = false
        end.position = move.position
        hud._input(end)
        _require((hero.get("input_axis") as Vector2).length() < 0.01, "Joystick release resets movement")
'''
    return exact(s,needle,extra+needle,"touch regression test")

rewrite("scripts/touch_hud.gd", japanese_hud)
rewrite("scripts/game_root.gd", japanese_story)
rewrite("tests/smoke.gd", touch_smoke)
print("ASTRA mobile build patch version 11.2 ready")
