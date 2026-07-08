from bot import safe_name

def test_safe_name_keeps_normal_name():
    assert safe_name("Hello") == "Hello"


def test_safe_name_replaces_invalid_characters():
    assert safe_name('A<B>C:D"E/F\\G|H?I*') == "A_B_C_D_E_F_G_H_I_"


def test_safe_name_strips_whitespace():
    assert safe_name("  Hello  ") == "Hello"