local serverScriptCode = [[
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local eventName = "PerfectShotEvent"
local perfectShotEvent = ReplicatedStorage:FindFirstChild(eventName)
if not perfectShotEvent then
    perfectShotEvent = Instance.new("RemoteEvent")
    perfectShotEvent.Name = eventName
    perfectShotEvent.Parent = ReplicatedStorage
end

local BALL_NAME = "Basketball"
local HOOP_NAME = "Hoop"

local function onPerfectShotRequest(player)
    local ball = workspace:FindFirstChild(BALL_NAME)
    local hoop = workspace:FindFirstChild(HOOP_NAME)

    if not ball or not hoop then return end

    local targetCFrame = hoop.CFrame + Vector3.new(0, 2, 0)

    if ball:IsA("BasePart") then
        for _, v in pairs(ball:GetDescendants()) do
            if v:IsA("BodyVelocity") or v:IsA("BodyForce") or v:IsA("BodyGyro") then
                v:Destroy()
            end
        end
        ball.CFrame = targetCFrame
        ball.Velocity = Vector3.new(0,0,0)
        pcall(function() ball.RotVelocity = Vector3.new(0,0,0) end)
    elseif ball.PrimaryPart then
        local primary = ball.PrimaryPart
        for _, v in pairs(ball:GetDescendants()) do
            if v:IsA("BodyVelocity") or v:IsA("BodyForce") or v:IsA("BodyGyro") then
                v:Destroy()
            end
        end
        primary.CFrame = targetCFrame
        primary.Velocity = Vector3.new(0,0,0)
        pcall(function() primary.RotVelocity = Vector3.new(0,0,0) end)
    end
end

perfectShotEvent.OnServerEvent:Connect(onPerfectShotRequest)
]]

loadstring(serverScriptCode)()
