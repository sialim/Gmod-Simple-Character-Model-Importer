DynamicModelImporter = DynamicModelImporter or {}
DynamicModelImporter.StaticRoot = "data_static/dynamic_model_importer/models"
DynamicModelImporter.LegacyAutorunPattern = "lua/autorun/*_sheepylord.lua"
DynamicModelImporter.Translations = {
    ["zh-CN"] = {
        ["Model Importer"] = "模型导入器",
        ["Dynamic Model Importer"] = "动态模型导入器",
        ["Spawn MMD Character Importer models."] = "生成 MMD Character Importer 模型。",
        ["Select a model in the menu. Left-click the world to spawn an NPC; right-click the world to spawn a ragdoll."] = "在菜单中选择模型。左键点击世界生成 NPC；右键点击世界生成布娃娃。",
        ["Shows models produced by MMD Character Importer. Select a row, then left-click the world to spawn an NPC or right-click the world to spawn a ragdoll."] = "显示由 MMD Character Importer 生成的模型。选择一行后，左键点击世界生成 NPC，或右键点击世界生成布娃娃。",
        ["Refresh model list"] = "刷新模型列表",
        ["Search models..."] = "搜索模型...",
        ["Friendly"] = "友好",
        ["Hostile"] = "敌对",
        ["Neutral"] = "中立",
        ["NPC health"] = "NPC 生命值",
        ["Shotgun"] = "霰弹枪",
        ["Pistol"] = "手枪",
        ["None"] = "无",
        ["Custom weapon class, for example weapon_smg1"] = "自定义武器类，例如 weapon_smg1",
        ["Manifest imported models"] = "清单导入模型",
        ["Legacy autorun models"] = "旧版 autorun 模型",
        ["Model"] = "模型",
        ["Category"] = "分类",
        ["Model path"] = "模型路径",
        ["PM"] = "玩家模型",
        ["yes"] = "是",
        ["no"] = "否",
        ["Selected model id"] = "已选模型 ID",
        ["Spawning only happens from the tool itself: left-click the world for NPC, right-click the world for ragdoll."] = "只能通过此工具生成：左键点击世界生成 NPC，右键点击世界生成布娃娃。",
        ["Model is not available: %s"] = "模型不可用：%s",
        ["Failed to create NPC class: %s"] = "创建 NPC 类失败：%s",
        ["Spawned NPC: %s"] = "已生成 NPC：%s",
        ["Failed to create ragdoll."] = "创建布娃娃失败。",
        ["Spawned ragdoll: %s"] = "已生成布娃娃：%s",
        ["Could not load model manifest."] = "无法加载模型清单。",
        ["Invalid model id."] = "模型 ID 无效。",
    },
    ["fr"] = {
        ["Model Importer"] = "Importateur de modèles",
        ["Dynamic Model Importer"] = "Importateur dynamique de modèles",
        ["Spawn MMD Character Importer models."] = "Fait apparaître les modèles de MMD Character Importer.",
        ["Select a model in the menu. Left-click the world to spawn an NPC; right-click the world to spawn a ragdoll."] = "Sélectionnez un modèle dans le menu. Clic gauche dans le monde pour créer un PNJ ; clic droit pour créer un ragdoll.",
        ["Shows models produced by MMD Character Importer. Select a row, then left-click the world to spawn an NPC or right-click the world to spawn a ragdoll."] = "Affiche les modèles produits par MMD Character Importer. Sélectionnez une ligne, puis faites un clic gauche dans le monde pour créer un PNJ ou un clic droit pour créer un ragdoll.",
        ["Refresh model list"] = "Actualiser la liste des modèles",
        ["Search models..."] = "Rechercher des modèles...",
        ["Friendly"] = "Amical",
        ["Hostile"] = "Hostile",
        ["Neutral"] = "Neutre",
        ["NPC health"] = "Santé du PNJ",
        ["Shotgun"] = "Fusil à pompe",
        ["Pistol"] = "Pistolet",
        ["None"] = "Aucun",
        ["Custom weapon class, for example weapon_smg1"] = "Classe d'arme personnalisée, par exemple weapon_smg1",
        ["Manifest imported models"] = "Modèles importés par manifeste",
        ["Legacy autorun models"] = "Modèles autorun hérités",
        ["Model"] = "Modèle",
        ["Category"] = "Catégorie",
        ["Model path"] = "Chemin du modèle",
        ["PM"] = "Modèle joueur",
        ["yes"] = "oui",
        ["no"] = "non",
        ["Selected model id"] = "ID du modèle sélectionné",
        ["Spawning only happens from the tool itself: left-click the world for NPC, right-click the world for ragdoll."] = "L'apparition se fait uniquement avec l'outil : clic gauche dans le monde pour un PNJ, clic droit pour un ragdoll.",
        ["Model is not available: %s"] = "Le modèle n'est pas disponible : %s",
        ["Failed to create NPC class: %s"] = "Impossible de créer la classe de PNJ : %s",
        ["Spawned NPC: %s"] = "PNJ créé : %s",
        ["Failed to create ragdoll."] = "Impossible de créer le ragdoll.",
        ["Spawned ragdoll: %s"] = "Ragdoll créé : %s",
        ["Could not load model manifest."] = "Impossible de charger le manifeste du modèle.",
        ["Invalid model id."] = "ID de modèle invalide.",
    },
    ["es-ES"] = {
        ["Model Importer"] = "Importador de modelos",
        ["Dynamic Model Importer"] = "Importador dinámico de modelos",
        ["Spawn MMD Character Importer models."] = "Genera modelos de MMD Character Importer.",
        ["Select a model in the menu. Left-click the world to spawn an NPC; right-click the world to spawn a ragdoll."] = "Selecciona un modelo en el menú. Haz clic izquierdo en el mundo para generar un NPC; clic derecho para generar un ragdoll.",
        ["Shows models produced by MMD Character Importer. Select a row, then left-click the world to spawn an NPC or right-click the world to spawn a ragdoll."] = "Muestra modelos producidos por MMD Character Importer. Selecciona una fila y luego haz clic izquierdo en el mundo para generar un NPC o clic derecho para generar un ragdoll.",
        ["Refresh model list"] = "Actualizar lista de modelos",
        ["Search models..."] = "Buscar modelos...",
        ["Friendly"] = "Amistoso",
        ["Hostile"] = "Hostil",
        ["Neutral"] = "Neutral",
        ["NPC health"] = "Salud del NPC",
        ["Shotgun"] = "Escopeta",
        ["Pistol"] = "Pistola",
        ["None"] = "Ninguno",
        ["Custom weapon class, for example weapon_smg1"] = "Clase de arma personalizada, por ejemplo weapon_smg1",
        ["Manifest imported models"] = "Modelos importados por manifiesto",
        ["Legacy autorun models"] = "Modelos autorun heredados",
        ["Model"] = "Modelo",
        ["Category"] = "Categoría",
        ["Model path"] = "Ruta del modelo",
        ["PM"] = "Modelo de jugador",
        ["yes"] = "sí",
        ["no"] = "no",
        ["Selected model id"] = "ID de modelo seleccionado",
        ["Spawning only happens from the tool itself: left-click the world for NPC, right-click the world for ragdoll."] = "La generación solo ocurre desde la herramienta: clic izquierdo en el mundo para NPC, clic derecho para ragdoll.",
        ["Model is not available: %s"] = "El modelo no está disponible: %s",
        ["Failed to create NPC class: %s"] = "No se pudo crear la clase de NPC: %s",
        ["Spawned NPC: %s"] = "NPC generado: %s",
        ["Failed to create ragdoll."] = "No se pudo crear el ragdoll.",
        ["Spawned ragdoll: %s"] = "Ragdoll generado: %s",
        ["Could not load model manifest."] = "No se pudo cargar el manifiesto del modelo.",
        ["Invalid model id."] = "ID de modelo no válido.",
    },
    ["ko"] = {
        ["Model Importer"] = "모델 가져오기",
        ["Dynamic Model Importer"] = "동적 모델 가져오기",
        ["Spawn MMD Character Importer models."] = "MMD Character Importer 모델을 생성합니다.",
        ["Select a model in the menu. Left-click the world to spawn an NPC; right-click the world to spawn a ragdoll."] = "메뉴에서 모델을 선택하세요. 월드에서 왼쪽 클릭하면 NPC가 생성되고, 오른쪽 클릭하면 래그돌이 생성됩니다.",
        ["Shows models produced by MMD Character Importer. Select a row, then left-click the world to spawn an NPC or right-click the world to spawn a ragdoll."] = "MMD Character Importer에서 만든 모델을 표시합니다. 행을 선택한 뒤 월드에서 왼쪽 클릭으로 NPC를, 오른쪽 클릭으로 래그돌을 생성하세요.",
        ["Refresh model list"] = "모델 목록 새로고침",
        ["Search models..."] = "모델 검색...",
        ["Friendly"] = "우호",
        ["Hostile"] = "적대",
        ["Neutral"] = "중립",
        ["NPC health"] = "NPC 체력",
        ["Shotgun"] = "샷건",
        ["Pistol"] = "권총",
        ["None"] = "없음",
        ["Custom weapon class, for example weapon_smg1"] = "사용자 지정 무기 클래스, 예: weapon_smg1",
        ["Manifest imported models"] = "매니페스트 가져온 모델",
        ["Legacy autorun models"] = "레거시 autorun 모델",
        ["Model"] = "모델",
        ["Category"] = "카테고리",
        ["Model path"] = "모델 경로",
        ["PM"] = "플레이어 모델",
        ["yes"] = "예",
        ["no"] = "아니요",
        ["Selected model id"] = "선택한 모델 ID",
        ["Spawning only happens from the tool itself: left-click the world for NPC, right-click the world for ragdoll."] = "생성은 이 도구에서만 됩니다. 월드에서 왼쪽 클릭은 NPC, 오른쪽 클릭은 래그돌입니다.",
        ["Model is not available: %s"] = "모델을 사용할 수 없습니다: %s",
        ["Failed to create NPC class: %s"] = "NPC 클래스를 만들 수 없습니다: %s",
        ["Spawned NPC: %s"] = "NPC 생성됨: %s",
        ["Failed to create ragdoll."] = "래그돌을 만들 수 없습니다.",
        ["Spawned ragdoll: %s"] = "래그돌 생성됨: %s",
        ["Could not load model manifest."] = "모델 매니페스트를 불러올 수 없습니다.",
        ["Invalid model id."] = "모델 ID가 올바르지 않습니다.",
    },
    ["ru"] = {
        ["Model Importer"] = "Импорт моделей",
        ["Dynamic Model Importer"] = "Динамический импорт моделей",
        ["Spawn MMD Character Importer models."] = "Создаёт модели MMD Character Importer.",
        ["Select a model in the menu. Left-click the world to spawn an NPC; right-click the world to spawn a ragdoll."] = "Выберите модель в меню. ЛКМ по миру создаёт NPC; ПКМ создаёт рэгдолл.",
        ["Shows models produced by MMD Character Importer. Select a row, then left-click the world to spawn an NPC or right-click the world to spawn a ragdoll."] = "Показывает модели, созданные MMD Character Importer. Выберите строку, затем нажмите ЛКМ по миру для NPC или ПКМ для рэгдолла.",
        ["Refresh model list"] = "Обновить список моделей",
        ["Search models..."] = "Поиск моделей...",
        ["Friendly"] = "Дружественный",
        ["Hostile"] = "Враждебный",
        ["Neutral"] = "Нейтральный",
        ["NPC health"] = "Здоровье NPC",
        ["Shotgun"] = "Дробовик",
        ["Pistol"] = "Пистолет",
        ["None"] = "Нет",
        ["Custom weapon class, for example weapon_smg1"] = "Пользовательский класс оружия, например weapon_smg1",
        ["Manifest imported models"] = "Модели из манифеста",
        ["Legacy autorun models"] = "Устаревшие autorun-модели",
        ["Model"] = "Модель",
        ["Category"] = "Категория",
        ["Model path"] = "Путь модели",
        ["PM"] = "Модель игрока",
        ["yes"] = "да",
        ["no"] = "нет",
        ["Selected model id"] = "ID выбранной модели",
        ["Spawning only happens from the tool itself: left-click the world for NPC, right-click the world for ragdoll."] = "Создание выполняется только этим инструментом: ЛКМ по миру для NPC, ПКМ для рэгдолла.",
        ["Model is not available: %s"] = "Модель недоступна: %s",
        ["Failed to create NPC class: %s"] = "Не удалось создать класс NPC: %s",
        ["Spawned NPC: %s"] = "NPC создан: %s",
        ["Failed to create ragdoll."] = "Не удалось создать рэгдолл.",
        ["Spawned ragdoll: %s"] = "Рэгдолл создан: %s",
        ["Could not load model manifest."] = "Не удалось загрузить манифест модели.",
        ["Invalid model id."] = "Недопустимый ID модели.",
    },
}

local DMI_LANGUAGE_ALIASES = {
    cn = "zh-CN",
    ["zh"] = "zh-CN",
    ["zh-cn"] = "zh-CN",
    ["zh_hans"] = "zh-CN",
    ["zh-hans"] = "zh-CN",
    ["schinese"] = "zh-CN",
    ["chinese"] = "zh-CN",
    ["zh-tw"] = "zh-CN",
    ["tchinese"] = "zh-CN",
    fr = "fr",
    french = "fr",
    es = "es-ES",
    ["es-es"] = "es-ES",
    spanish = "es-ES",
    ko = "ko",
    ["ko-kr"] = "ko",
    koreana = "ko",
    korean = "ko",
    ru = "ru",
    russian = "ru",
}

function DynamicModelImporter.NormalizeLanguageCode(raw)
    local normalized = tostring(raw or "en"):lower():gsub("_", "-")
    return DMI_LANGUAGE_ALIASES[normalized] or DMI_LANGUAGE_ALIASES[normalized:match("^[^%-]+") or ""] or "en"
end

function DynamicModelImporter.LanguageCode()
    if not CLIENT then return "en" end
    return DynamicModelImporter.NormalizeLanguageCode(GetConVarString("gmod_language") or "en")
end

function DynamicModelImporter.L(raw)
    local text = tostring(raw or "")
    if not CLIENT then return text end
    local languageTable = DynamicModelImporter.Translations[DynamicModelImporter.LanguageCode()]
    if languageTable and languageTable[text] then
        return languageTable[text]
    end
    return text
end

function DynamicModelImporter.LF(raw, ...)
    local ok, formatted = pcall(string.format, DynamicModelImporter.L(raw), ...)
    if ok then return formatted end
    return DynamicModelImporter.L(raw)
end

local function starts_with(value, prefix)
    return string.sub(value, 1, #prefix) == prefix
end

local function trim(value)
    return tostring(value or ""):match("^%s*(.-)%s*$") or ""
end

function DynamicModelImporter.NormalizeID(raw)
    raw = tostring(raw or ""):lower()
    raw = raw:gsub("\\", "/")
    raw = raw:gsub("%.json$", "")
    raw = raw:gsub("^/+", "")
    raw = raw:gsub("/+$", "")
    raw = raw:gsub("[^a-z0-9_%-/]", "")
    if raw == "" then return nil end
    if string.find(raw, "../", 1, true) or string.find(raw, "..\\", 1, true) then return nil end
    if string.find(raw, "//", 1, true) then return nil end
    return raw
end

function DynamicModelImporter.NormalizeModelPath(raw)
    raw = tostring(raw or "")
    raw = raw:gsub("\\", "/")
    raw = raw:gsub("^/+", "")
    raw = trim(raw)
    local lower = string.lower(raw)
    if raw == "" then return nil end
    if string.find(raw, "..", 1, true) then return nil end
    if not starts_with(lower, "models/") then return nil end
    if not string.match(lower, "%.mdl$") then return nil end
    return raw
end

local function warn(message)
    print("[Dynamic Model Importer] " .. tostring(message))
end

local function manifest_to_entry(manifest, fallbackID)
    if not istable(manifest) then return nil end
    local paths = istable(manifest.paths) and manifest.paths or {}
    local modelPath = DynamicModelImporter.NormalizeModelPath(paths.model or manifest.model_path)
    if not modelPath then return nil end
    local id = DynamicModelImporter.NormalizeID(manifest.manifest_id or manifest.model_id or fallbackID)
    if not id then return nil end
    local pmPath = DynamicModelImporter.NormalizeModelPath(paths.player_model or manifest.player_model_path or "")
    return {
        model_id = id,
        display_name = tostring(manifest.display_name or manifest.model_name or id),
        category_readable = tostring(manifest.category_readable or manifest.character_category or ""),
        character_category = tostring(manifest.character_category or ""),
        author = tostring(manifest.author or ""),
        model_path = modelPath,
        player_model_path = pmPath or "",
        has_player_model = pmPath ~= nil and pmPath ~= "",
        arms_model_path = DynamicModelImporter.NormalizeModelPath(paths.arms_model or "") or "",
        friendly_icon = tostring(paths.friendly_icon or ""),
        enemy_icon = tostring(paths.enemy_icon or ""),
        npc_defaults = istable(manifest.npc_defaults) and manifest.npc_defaults or {},
        legacy = tobool(manifest.legacy),
    }
end

local parse_legacy_autorun

function DynamicModelImporter.LoadManifest(modelID)
    local safeID = DynamicModelImporter.NormalizeID(modelID)
    if not safeID then return nil, "Invalid model id." end
    local path = DynamicModelImporter.StaticRoot .. "/" .. safeID .. ".json"
    local raw = file.Read(path, "GAME")
    if not raw then
        if parse_legacy_autorun then
            local legacy = parse_legacy_autorun("lua/autorun/" .. safeID .. ".lua")
            if legacy then return legacy end
            local legacyFiles = file.Find(DynamicModelImporter.LegacyAutorunPattern, "GAME", "nameasc")
            for _, name in ipairs(legacyFiles or {}) do
                if DynamicModelImporter.NormalizeID(name) == safeID then
                    legacy = parse_legacy_autorun("lua/autorun/" .. name)
                    if legacy then return legacy end
                end
            end
        end
        return nil, "Manifest not found: " .. path
    end
    local parsed = util.JSONToTable(raw, true, true)
    local entry = manifest_to_entry(parsed, safeID)
    if not entry then return nil, "Manifest is invalid: " .. path end
    return entry
end

local function add_seen(results, seen, entry)
    if not entry or not entry.model_id or seen[entry.model_id] then return end
    seen[entry.model_id] = true
    results[#results + 1] = entry
end

local function legacy_id_from_path(path)
    local name = tostring(path or ""):match("([^/\\]+)%.lua$") or tostring(path or "")
    return DynamicModelImporter.NormalizeID(name)
end

parse_legacy_autorun = function(path)
    local raw = file.Read(path, "GAME")
    if not raw then return nil end
    local display, pmPath = raw:match('player_manager%.AddValidModel%(%s*"([^"]+)"%s*,%s*"([^"]+)"')
    local category = raw:match('local%s+Category%s*=%s*"([^"]+)"') or ""
    local modelPath = raw:match('Model%s*=%s*"([^"]+%.mdl)"')
    local id = legacy_id_from_path(path)
    if not modelPath or not id then return nil end
    local manifest = {
        manifest_id = id,
        display_name = display or id,
        category_readable = category,
        paths = {
            model = modelPath,
            player_model = pmPath or "",
        },
        legacy = true,
        npc_defaults = {
            relation = "friendly",
            health = 100,
            weapon = "weapon_smg1",
        },
    }
    return manifest_to_entry(manifest, id)
end

function DynamicModelImporter.ListAvailableModels()
    local results = {}
    local seen = {}
    local files = file.Find(DynamicModelImporter.StaticRoot .. "/*.json", "GAME", "nameasc")
    for _, name in ipairs(files or {}) do
        local id = DynamicModelImporter.NormalizeID(name)
        if id then
            local entry, err = DynamicModelImporter.LoadManifest(id)
            if entry then
                add_seen(results, seen, entry)
            elseif err then
                warn(err)
            end
        end
    end

    local legacyFiles = file.Find(DynamicModelImporter.LegacyAutorunPattern, "GAME", "nameasc")
    for _, name in ipairs(legacyFiles or {}) do
        local entry = parse_legacy_autorun("lua/autorun/" .. name)
        add_seen(results, seen, entry)
    end

    table.sort(results, function(a, b)
        local ac = string.lower(a.category_readable or "")
        local bc = string.lower(b.category_readable or "")
        if ac ~= bc then return ac < bc end
        return string.lower(a.display_name or a.model_id or "") < string.lower(b.display_name or b.model_id or "")
    end)
    return results
end

local function sanitize_relation(value)
    value = string.lower(tostring(value or "friendly"))
    if value ~= "friendly" and value ~= "hostile" and value ~= "neutral" then
        return "friendly"
    end
    return value
end

local function sanitize_weapon(value)
    value = tostring(value or ""):gsub("[^%w_]", "")
    if value ~= "" and not starts_with(value, "weapon_") then
        return ""
    end
    return value
end

local function safe_health(value)
    return math.Clamp(math.floor(tonumber(value) or 100), 1, 9999)
end

local function valid_model_for_spawn(modelPath)
    if not DynamicModelImporter.NormalizeModelPath(modelPath) then return false end
    if util and util.IsValidModel then
        return util.IsValidModel(modelPath)
    end
    return file.Exists(modelPath, "GAME")
end

if SERVER then
    local function chat(ply, message, ...)
        if IsValid(ply) then
            local args = {...}
            if net then
                net.Start("dynamic_model_importer_chat")
                    net.WriteString(tostring(message))
                    net.WriteUInt(math.min(#args, 8), 4)
                    for i = 1, math.min(#args, 8) do
                        net.WriteString(tostring(args[i]))
                    end
                net.Send(ply)
            else
                ply:ChatPrint("[Dynamic Model Importer] " .. DynamicModelImporter.LF(message, unpack(args)))
            end
        end
    end

    local function apply_npc_relationship(npc, ply, relation)
        local disp = D_LI
        if relation == "hostile" then
            disp = D_HT
        elseif relation == "neutral" then
            disp = D_NU
        end
        if npc.AddEntityRelationship then
            npc:AddEntityRelationship(ply, disp, 99)
        end
        if ply.AddEntityRelationship then
            ply:AddEntityRelationship(npc, disp, 99)
        end
    end

    local function spawn_position(ply, trace)
        trace = istable(trace) and trace or ply:GetEyeTrace()
        local pos = trace.HitPos + trace.HitNormal * 12
        local ang = Angle(0, ply:EyeAngles().y + 180, 0)
        return pos, ang
    end

    local function npc_spec(manifest, relation)
        local defaults = istable(manifest.npc_defaults) and manifest.npc_defaults or {}
        local spec = istable(defaults[relation]) and defaults[relation] or {}
        if relation == "hostile" then
            return spec.class or "npc_combine_s", spec
        end
        return spec.class or "npc_citizen", spec
    end

    local function spawn_npc(ply, manifest, relation, health, weapon, trace)
        local modelPath = manifest.model_path
        if not valid_model_for_spawn(modelPath) then
            chat(ply, "Model is not available: %s", modelPath)
            return false
        end
        local class, spec = npc_spec(manifest, relation)
        local ent = ents.Create(class)
        if not IsValid(ent) then
            chat(ply, "Failed to create NPC class: %s", class)
            return false
        end
        local pos, ang = spawn_position(ply, trace)
        ent:SetPos(pos)
        ent:SetAngles(ang)
        ent:SetModel(modelPath)
        for key, val in pairs(istable(spec.keyvalues) and spec.keyvalues or {}) do
            ent:SetKeyValue(tostring(key), tostring(val))
        end
        if weapon ~= "" then
            ent:SetKeyValue("additionalequipment", weapon)
        end
        ent:Spawn()
        ent:Activate()
        ent:SetHealth(health)
        if ent.SetMaxHealth then ent:SetMaxHealth(health) end
        if weapon ~= "" and ent.Give then
            pcall(function() ent:Give(weapon) end)
        end
        apply_npc_relationship(ent, ply, relation)
        ent:DropToFloor()
        undo.Create("Dynamic Model Importer NPC")
            undo.AddEntity(ent)
            undo.SetPlayer(ply)
        undo.Finish()
        cleanup.Add(ply, "npcs", ent)
        chat(ply, "Spawned NPC: %s", manifest.display_name or manifest.model_id)
        return true
    end

    local function spawn_ragdoll(ply, manifest, trace)
        local modelPath = manifest.model_path
        if not valid_model_for_spawn(modelPath) then
            chat(ply, "Model is not available: %s", modelPath)
            return false
        end
        local ent = ents.Create("prop_ragdoll")
        if not IsValid(ent) then
            chat(ply, "Failed to create ragdoll.")
            return false
        end
        local pos, ang = spawn_position(ply, trace)
        ent:SetPos(pos)
        ent:SetAngles(ang)
        ent:SetModel(modelPath)
        ent:Spawn()
        ent:Activate()
        local phys = ent:GetPhysicsObject()
        if IsValid(phys) then phys:Wake() end
        undo.Create("Dynamic Model Importer Ragdoll")
            undo.AddEntity(ent)
            undo.SetPlayer(ply)
        undo.Finish()
        cleanup.Add(ply, "ragdolls", ent)
        chat(ply, "Spawned ragdoll: %s", manifest.display_name or manifest.model_id)
        return true
    end

    function DynamicModelImporter.SpawnFromRequest(ply, modelID, action, relation, health, weapon, trace)
        local manifest, err = DynamicModelImporter.LoadManifest(modelID)
        if not manifest then
            chat(ply, err or "Could not load model manifest.")
            return false
        end
        action = string.lower(tostring(action or "npc"))
        relation = sanitize_relation(relation)
        health = safe_health(health)
        weapon = sanitize_weapon(weapon)
        if action == "ragdoll" then
            return spawn_ragdoll(ply, manifest, trace)
        end
        if weapon == "" then
            local defaults = istable(manifest.npc_defaults) and manifest.npc_defaults or {}
            local relationSpec = istable(defaults[relation]) and defaults[relation] or {}
            weapon = sanitize_weapon(relationSpec.weapon or defaults.weapon or "")
        end
        return spawn_npc(ply, manifest, relation, health, weapon, trace)
    end
end
