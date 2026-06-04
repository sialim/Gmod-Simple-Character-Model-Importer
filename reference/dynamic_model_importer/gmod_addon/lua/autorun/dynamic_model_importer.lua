if SERVER then
    AddCSLuaFile("dynamic_model_importer/sh_core.lua")
    util.AddNetworkString("dynamic_model_importer_request_list")
    util.AddNetworkString("dynamic_model_importer_send_list")
    util.AddNetworkString("dynamic_model_importer_chat")
end

include("dynamic_model_importer/sh_core.lua")

local function write_entry(entry)
    net.WriteString(tostring(entry.model_id or ""))
    net.WriteString(tostring(entry.display_name or entry.model_id or ""))
    net.WriteString(tostring(entry.category_readable or ""))
    net.WriteString(tostring(entry.model_path or ""))
    net.WriteBool(tobool(entry.has_player_model))
    net.WriteBool(tobool(entry.legacy))
end

if SERVER then
    local function send_model_list(ply)
        local list = DynamicModelImporter.ListAvailableModels()
        net.Start("dynamic_model_importer_send_list")
            net.WriteUInt(#list, 16)
            for _, entry in ipairs(list) do
                write_entry(entry)
            end
        net.Send(ply)
    end

    net.Receive("dynamic_model_importer_request_list", function(_, ply)
        if not IsValid(ply) then return end
        send_model_list(ply)
    end)

else
    DynamicModelImporter.LastModelList = DynamicModelImporter.LastModelList or {}

    net.Receive("dynamic_model_importer_chat", function()
        local message = net.ReadString()
        local count = net.ReadUInt(4)
        local args = {}
        for i = 1, count do
            args[i] = net.ReadString()
        end
        local unpack_args = unpack or table.unpack
        chat.AddText(Color(120, 190, 255), "[Dynamic Model Importer] ", color_white, DynamicModelImporter.LF(message, unpack_args(args)))
    end)

    net.Receive("dynamic_model_importer_send_list", function()
        local count = net.ReadUInt(16)
        local list = {}
        for i = 1, count do
            list[i] = {
                model_id = net.ReadString(),
                display_name = net.ReadString(),
                category_readable = net.ReadString(),
                model_path = net.ReadString(),
                has_player_model = net.ReadBool(),
                legacy = net.ReadBool(),
            }
        end
        DynamicModelImporter.LastModelList = list
        hook.Run("DynamicModelImporterListUpdated", list)
    end)

    concommand.Add("dynamic_model_importer_refresh", function()
        net.Start("dynamic_model_importer_request_list")
        net.SendToServer()
    end)

end
