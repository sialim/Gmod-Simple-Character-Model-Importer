player_manager.AddValidModel( "Yumemizuki_mizuki", "models/sheepylord/genshin_impact/yumemizuki.mdl" );
player_manager.AddValidHands( "Yumemizuki_mizuki", "models/sheepylord/genshin_impact/yumemizuki_arms.mdl", 0, "00000000" )

local Category = "Genshin Impact"

local NPC = {
    Name = "Yumemizuki_F",
    Class = "npc_citizen",
    Model = "models/sheepylord/genshin_impact/yumemizuki.mdl",
    Health = "100",
    KeyValues = { citizentype = 4 },
    Weapons = { "weapon_smg1" },
    Category = Category
}

list.Set("NPC", "Yumemizuki_F", NPC)

local NPC = {
    Name = "Yumemizuki_E",
    Class = "npc_combine_s",
    Model = "models/sheepylord/genshin_impact/yumemizuki.mdl",
    Health = "100",
    Numgrenades = "4",
    Weapons = { "weapon_ar2" },
    Category = Category
}

list.Set("NPC", "Yumemizuki_E", NPC)
