import numpy as np
import os
import bpy

# Specifiy your Work Folder
work_path = np.load("workpath.npy", allow_pickle = True)[0]

# Select The Main Armature
try:
    bpy.ops.mesh.select_all(action='DESELECT')
except:
    pass

try:
    bpy.ops.object.select_all(action='DESELECT')
except:
    pass

special_replacement_dict = {
    "□": "mouth_square",
    "▲": "mouth_tri",
    "Anger": "brows_angry",
    "Anger Left": "brows_angry_left",
    "Anger Right": "brows_angry_right",
    "Serious": "brows_serious",
    "Sad": "brows_sad",
    "Sadness": "brows_worry",
    "Sadness Left": "brows_worry_left",
    "Sadness Right": "brows_worry_right",
    "Is It? Ch": "brows_questioning",
    "Cheerful": "brows_happy",
    "Cheerful Left": "brows_happy_left",
    "Cheerful Right": "brows_happy_right",
    "Shame Ch": "brows_flat",
    "Shame Ch Left": "brows_flat_left",
    "Shame Ch Right": "brows_flat_right",
    "Lower": "brows_lower",
    "Lower Left": "brows_lower_left",
    "Lower Right": "brows_lower_right",
    "Upper": "brows_up",
    "Upper Left": "brows_up_left",
    "Upper Right": "brows_up_right",
    "Front": "brows_closer",
    "Front Left": "brows_closer_left",
    "Front Right": "brows_closer_right",
    "Surprise": "brows_surprise",
    "Cheerful 2": "brows_happy_2",
    "Flat Line": "brows_flat",
    "Enter": "brows_close",
    "Blink": "blink",
    "Wink 2": "eye_blink_left",
    "Blink Happy": "eye_blink_happy",
    "Wink": "eye_blink_happy_left",
    "Wink 2 Right": "eye_blink_right",
    "Wink Right": "eye_blink_happy_right",
    "Blink Happy2": "eye_blink_happy_2",
    "Blink Happy Eye": "eyes_smug",
    "Sad Eye": "eyes_sad",
    "Droopy Eye": "eyes_droppy",
    "Delight FacialExpression": "eyes_smug",
    "Delight FacialExpression2": "eyes_smug_2",
    "Charity Love": "eyes_peaceful",
    "Charity Love2": "eyes_peaceful_2",
    "Surprised": "eyes_surprised",
    "Look Open": "eyes_enlarge",
    "Surprised Vinegar": "eyes_surprised_2",
    "Stare": "eyes_stare",
    "Stare2": "eyes_stare_2",
    "Slant": "eyes_slant",
    "Slant2": "eyes_slant_2",
    "Ah": "mouth_a",
    "Ah2": "mouth_a_2",
    "Ah 2": "mouth_a_2",
    "Ah 3": "mouth_a_3",
    "Ch": "mouth_i",
    "Ch 1": "mouth_ch_1",
    "Ch 2": "mouth_ch_2",
    "U": "mouth_u",
    "E": "mouth_e",
    "E E ?": "mouth_e_questioning",
    "Oh": "mouth_o",
    "Hmm": "mouth_neutral",
    "Grin": "mouth_grin",
    "Grin2": "mouth_grin_2",
    "Grin 2": "mouth_grin_2",
    "Grin3": "mouth_grin_3",
    "Grin 3": "mouth_grin_3",
    "Grin Right": "mouth_grin_right",
    "Grin Left": "mouth_grin_left",
    "Lick": "mouth_lick",
    "Mouth Side Narrow Eye": "mouth_narrow",
    "Mmm": "mouth_unhappy_thinking",
    "Anger Did": "mouth_anger",
    "Anger Did2": "mouth_anger_2",
    "Oh Small Difference Ch": "mouth_i_small",
    "Kiss": "mouth_kiss",
    "Mouth": "mouth_gasp",
    "Mouth Horn Lower": "mouth_sad",
    "Mouth Horn Raise": "mouth_smile",
    "Ch2": "mouth_i_2",
    "E2": "mouth_e_2",
    "Mouth Lower": "mouth_lower",
    "Big Mouth": "mouth_big",
    "Oh2": "mouth_o_2",
    "Mouth Side Ash": "mouth_small",
    "Defeat ω": "mouth_defeat",
    "Pain Body": "mouth_pain",
    "Pain Body2": "mouth_pain_2",
    "Pain Body3": "mouth_pain_3",
    "Mouth Side Ash2": "mouth_small_2",
    "V": "mouth_smile_v",
    "ω": "mouth_cat",
    "ω□": "mouth_cat_square",
    "Wa": "mouth_wa",
    "Wa1": "mouth_wa_2",
    "Wa2": "mouth_wa_3",
    "∧": "mouth_closed_tri",
    "Mouth Horn Lower2": "mouth_sad_2",
    "Mouth Upper": "mouth_upper",
    "Mouth Side Widen": "mouth_widen",
    "Anxiety Vinegar Ru": "mouth_disgust",
    "Anxiety Vinegar Ru2": "mouth_disgust_2",
    "E3": "mouth_e_3",
    "e-": "mouth_e_4",
    "Smile": "mouth_smile",
    "Smile2": "mouth_smile2",
    "Tooth": "mouth_teeth_remove",
    "Tooth Upper": "mouth_teeth_hide_upper",
    "Tooth Lower": "mouth_teeth_hide_lower",
    "Teeth Elimination": "mouth_teeth_hide",
    "Teeth Elimination2": "mouth_teeth_hide_2",
    "Skin Double Teeth": "mouth_teeth_vampire",
    "Skin Double Teeth Right": "mouth_teeth_vampire_right",
    "Skin Double Teeth Left": "mouth_teeth_vampire_left",
    "Close><": "eyes_teehee",
    "Hachu Eye": "misc_OO",
    "Calm": "eyes_calm",
    "Calm Left": "eyes_calm_left",
    "Calm Right": "eyes_calm_right",
    "Anger Eye": "eyes_anger",
    "Jito Eye": "eyes_staring",
    "Eye Horn Upper": "eyes_outer_upper",
    "Eye Horn Lower": "eyes_outer_lower",
    "Lower Eye Upper": "eyes_lower_upper",
    "Highlight Elimination": "eyes_hightlight_hide",
    "White Eye": "eyes_pupil_hide",
    "Heart": "eyes_heart",
    "Star Eye": "eyes_star_eye",
    "Pupil": "eyes_pupil_small",
    "Tears": "misc_tears",
    "Absolute": "misc_blush",
    "Sweat Face": "misc_sweat",
    "111": "misc_awkward",
    "1111":  "misc_unwell",
    "11+":  "misc_uppershy",
    "Anger.001":  "emote_angry", 
    "!":  "emote_surprise", 
    "?":  "emote_question", 
    "! !":  "emote_shock", 
    "Sweat":  "emote_sweat", 
    "FaceRed": "face_red",
    "#": "emote_unsatisified",
    "#2": "emote_unsatisified_left",
    "ZZZ": "emote_sleepy",
    "Hachu": "emote_awkward",
    "……": "emote_speechless",
    
    "Wink2": "eye_blink_left",
    "eyeclose7" : "eye_blink_right",
    "eyeclose8" : "eye_blink_happy_right",
    "hitomih": "eyes_highlightdown",
    "hitomis": "eyes_iris_small",
    "Blush": "misc_blush",
    "Blush2": "misc_blush_2",
    "hoho2": "misc_blush_full",
    "hohol": "misc_blush_lower",
    "shock":  "misc_unwell",
    "mouthuphalf": "mouth_grin_2",
    "nosefook": "misc_nose_up",
    "Aha": "mouth_a",
    "Uu": "mouth_u",
    "mouthdw": "mouth_sad",
    "mouthhe": "mouth_neutral",
    "Chi": "mouth_i",
    "tangopen": "mouth_tongue_wide",
    "tangout": "mouth_tongue_out",
    "tangup": "mouth_tongue_up",
    "tear1": "misc_tears_1",
    "tear2": "misc_tears_2",
    "tear3": "misc_tears_3",
    "toothoff": "mouth_teeth_remove",
    "yodare": "misc_sweat",
    "Ah Ah": "mouth_aah",
    "U 2": "mouth_un",
    "Oh 2": "mouth_ooh",
    "Hmm 2": "mouth_hmm",
    
    "Up": "eyes_look_up",
    "Pupil_Up": "eyes_look_up",
    "Down": "eyes_look_down",
    "Pupil_Down": "eyes_look_down",
    "Left":  "eyes_look_left",
    "Pupil_L":  "eyes_look_left",
    "Right":  "eyes_look_right",
    "Pupil_R":  "eyes_look_right",
    "HorrorChild !": "eyes_hide",
    "Pupil_Scale":  "eyes_small",
    "Camera Eye": "eyes_look_camera",
    "Mouth Side Shrink": "mouth_shrink",
    "Jaw Front": "mouth_jaw_front",
    "Jaw Upper": "mouth_jaw_upper",
    "Jaw Left":  "mouth_jaw_left",
    "Jaw Right":  "mouth_jaw_right",
    "Mouth Left": "mouth_left",
    "Mouth Right": "mouth_right",
    "Nose Upper": "nose_upper",
    "Nose Lower": "nose_lower",
    
    "E_Stare": "eyes_enlarge",
    "B_Cheerful": "brows_cheerful",
    "B_Flat": "brows_flat",
    "E_Anger": "eyes_anger",
    "B_AH_R": "brows_serious_right",
    "B_AH_L": "brows_serious_left",
    "E_Anger": "eyes_anger",
    "E_Sad": "eyes_sad",
    "M_OpenSmall": "mouth_open_small",
    "M_Laugh": "mouth_grin",

    "M_Scared": "mouth_scared",
    "M_ScaredTooth": "mouth_pain",
    "M_Anger": "mouth_anger",
    "M_Trapezoid": "mouth_trapezoid",
    "M_O": "mouth_oh",
    "M_A": "mouth_ah",
    "M_Nutcracker": "mouth_middle",
    "C_M_Distant": "mouth_open_thin",
    "P_Nose_Up": "nose_up",
    "P_Nose_Down": "nose_down",
    
    "P_M_Up_Add": "mouth_up",
    "P_M_Down_Add": "mouth_down",
    "P_M_RMove_Add": "mouth_right",
    "P_M_LMove_Add": "mouth_left",
    "P_M_Scale_Add": "mouth_shrink",
}

bpy.data.objects["Armature"].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['Armature']
bpy.data.screens["Scripting"].areas[0].spaces[0].context = 'DATA'
bpy.context.object.data.show_names = True
bpy.ops.object.editmode_toggle()

spine_bone_existence = [False, False, False, False, False]

for bone_instance in bpy.context.object.data.bones:
    if bone_instance.name == "ValveBiped.Bip01_Pelvis":
        spine_bone_existence[0] = True
    if bone_instance.name == "ValveBiped.Bip01_Spine":
        spine_bone_existence[1] = True
    if bone_instance.name == "ValveBiped.Bip01_Spine1":
        spine_bone_existence[2] = True
    if bone_instance.name == "ValveBiped.Bip01_Spine2":
        spine_bone_existence[3] = True
    if bone_instance.name == "ValveBiped.Bip01_Spine4":
        spine_bone_existence[4] = True
    
print(spine_bone_existence)

if not all(spine_bone_existence):
    raise Exception("Not all Spine Bones were fixed, please double check")
else:
    bpy.context.object.data.show_names = False
    bpy.ops.object.editmode_toggle()
    
# Select The Main Mesh
try:
    bpy.ops.mesh.select_all(action='DESELECT')
except:
    pass

try:
    bpy.ops.object.select_all(action='DESELECT')
except:
    pass

bpy.data.objects["Body"].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['Body']
bpy.data.screens["Scripting"].areas[0].spaces[0].context = 'DATA'

for shape_key in bpy.data.shape_keys['Key'].key_blocks:
    shapekey_name = shape_key.name
    
    if shapekey_name in special_replacement_dict:
        shape_key.name = special_replacement_dict[shapekey_name]
        shapekey_name = special_replacement_dict[shapekey_name]
    
    print(shapekey_name)
    for c in shapekey_name.replace(" ", "").replace("_", ""):
        if not c.isalnum():
            raise Exception(f"ShapeKey {shapekey_name} contains special character in its name, please rename manually.")
        else:
            pass
    
# Save Current Blend as Ckpt
bpy.ops.wm.save_as_mainfile(filepath = os.path.join(work_path, "2_Blends\\3.blend"))