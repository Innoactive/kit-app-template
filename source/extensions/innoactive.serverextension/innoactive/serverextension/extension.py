import os
import omni.ext
import omni.ui as ui
import omni.usd
import omni.kit
import omni.kit.commands
import json
import carb
import carb.tokens
import carb.settings
import asyncio  # Import asyncio for the delay
from pxr import Usd, UsdGeom, Gf
from omni.kit.viewport.utility import get_active_viewport


# Functions and vars are available to other extensions as usual in python: `innoactive.serverextension.some_public_function(x)`
def set_usd(usd):
    carb.log_info(f"set_usd '{usd}'")
    MyExtension.set_usd(MyExtension, usd)


# Any class derived from `omni.ext.IExt` in the top level module (defined in `python.modules` of `extension.toml`) will
# be instantiated when the extension gets enabled, and `on_startup(ext_id)` will be called.
# Later when the extension gets disabled on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is the current extension id. It can be used with the extension manager to query additional information,
    # like where this extension is located on the filesystem.
    empty_stage = "usd/Empty/Stage.usd"
    usd_to_load = ""
    default_usd = "usd/JetEngine/jetengine.usd"
    layout_json = "./InnoactiveLayout.json"
    interface_mode = "screen"
    stage = None  # Reference to the USD stage
    settings = carb.settings.get_settings()
    message_bus = None

    def __init__(self):
        super().__init__()

        self._subscriptions = []  # Holds subscription pointers
        self.message_bus = omni.kit.app.get_app().get_message_bus_event_stream()

    def _on_execute_action(self, event: carb.events.IEvent) -> None:
        if event.type != carb.events.type_from_string("executeAction"):
            return

        message = event.payload.get("message", None)
        if message is None:
            carb.log_error(
                f"[innoactive.serverextension] Received executeAction event without message: {event.payload}"
            )
            return

        try:
            parsed_message = json.loads(message)

            carb.log_info(
                f"[innoactive.serverextension] Received executeAction event: {parsed_message}"
            )

            desired_action = parsed_message.get("actionType")
            # play
            if desired_action == "play":
                omni.kit.commands.execute("ToolbarPlayButtonClicked")
            elif desired_action == "pause":
                omni.kit.commands.execute("ToolbarPauseButtonClicked")
            elif desired_action == "stop":
                # stop
                omni.kit.commands.execute("ToolbarStopButtonClicked")
            else:
                carb.log_error(
                    f"[innoactive.serverextension] Unknown action: {desired_action}"
                )
        except json.JSONDecodeError:
            carb.log_error(
                f"[innoactive.serverextension] Failed to parse message as JSON: {message}"
            )

    def set_usd(self, usd_file):
        carb.log_info(f"internal set_usd '{usd_file}'")
        self.usd_to_load = usd_file

    def _ensure_camera_temp(
        self, camera_path="/SessionLayer/XRCam", position=(0, 0, 0)
    ):
        """
        Ensures a temporary camera with the specified name exists in the stage.
        If not, it creates one at the given position.
        Sets the camera as the active camera for the viewport.
        """
        if not self.stage:
            carb.log_warning("Stage is not loaded.")
            return

        # Check if the camera already exists
        camera_prim = self.stage.GetPrimAtPath(camera_path)
        if camera_prim and camera_prim.IsValid():
            carb.log_info(f"Camera '{camera_path}' already exists.")
        else:
            carb.log_info(
                f"Camera '{camera_path}' not found. Adding it to the stage (temporary)."
            )
            try:
                # Add the camera in the session layer
                with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
                    camera_prim = self.stage.DefinePrim(camera_path, "Camera")
                    camera = UsdGeom.Camera(camera_prim)

                    # Set camera's translation
                    # camera_prim.GetAttribute("xformOp:translate").Set(Gf.Vec3d(*position))

                carb.log_info(
                    f"Temporary Camera '{camera_path}' added successfully at {position}."
                )
            except Exception as e:
                carb.log_info(
                    f"Failed to add temporary Camera '{camera_path}': {str(e)}"
                )

        # Set the camera as active in the viewport
        # self._set_active_camera_in_viewport(camera_path)

    def _set_active_camera_in_viewport(self, camera_path):
        """
        Sets the specified camera as the active camera in the active viewport.
        """
        try:
            viewport = get_active_viewport()
            if not viewport:
                raise RuntimeError("No active Viewport")
            viewport.camera_path = camera_path
            carb.log_info(f"Camera '{camera_path}' set as active in the viewport.")
        except Exception as e:
            carb.log_info(
                f"Failed to set active camera in the viewport '{camera_path}': {str(e)}"
            )

    def _on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.OPENED):
            carb.log_info("Stage has fully loaded!")
            stage_path = self.usd_context.get_stage_url()
            carb.log_info(f"Stage {stage_path}")

            # Get the stage and store it at the class level
            self.stage = self.usd_context.get_stage()
            if not self.stage:
                carb.log_info("Unable to retrieve stage.")
                return

            if stage_path.startswith("anon:"):
                delay = 1
                carb.log_info(
                    f"empty_stage loaded. Now loading USD file with delay of {delay} seconds"
                )
                asyncio.ensure_future(self._delayed_load_usd(delay))
            else:
                carb.log_info(f"USD loaded: {stage_path}")
                self.load_layout()

    def load_usd(self, usd_file: str, log_errors=True):
        """
        Class method to load a USD file.
        Args:
            usd_file (str): Path to the USD file to load.
            log_errors (bool): Whether to log errors if loading fails.
        """
        if not isinstance(usd_file, str):
            if log_errors:
                carb.log_error(f"Invalid USD path: {usd_file}. Must be a string.")
            return

        try:
            carb.log_info(f"Loading USD file: {usd_file}")
            omni.usd.get_context().open_stage(usd_file)

            # If AR, then ensure the XRCam camera exists
            if self.interface_mode == "ar":
                self._ensure_camera_temp("/SessionLayer/XRCam", position=(0, 0, 0))
                self._apply_ar_settings_after_load()

        except Exception as e:
            if log_errors:
                carb.log_error(f"Failed to open USD file {usd_file}: {str(e)}")

    async def _delayed_load_usd(self, delay=10):

        await asyncio.sleep(delay)
        self.load_usd(usd_file=self.usd_to_load)

    def load_layout(self, log_errors=True):

        workspace_file = f"./InnoactiveLayout.{self.interface_mode}.json"

        if not os.path.exists(workspace_file):
            if log_errors:
                carb.log_error(f"Layout file does not exist: {workspace_file}")
            return

        try:
            result, _, content = omni.client.read_file(workspace_file)
            if result != omni.client.Result.OK:
                if log_errors:
                    carb.log_error(
                        f"Can't read the workspace file {workspace_file}, error code: {result}"
                    )
                return

            try:
                data = json.loads(memoryview(content).tobytes().decode("utf-8"))
            except Exception as e:
                if log_errors:
                    carb.log_error(
                        f"Failed to parse JSON from {workspace_file}: {str(e)}"
                    )
                return

            ui.Workspace.restore_workspace(data, False)
            carb.log_info(f"The workspace is loaded from {workspace_file}")
        except Exception as e:
            if log_errors:
                carb.log_error(f"Unexpected error while loading layout: {str(e)}")

    def _apply_ar_settings_after_load(self):
        carb.log_info("applying AR settings after load")
        # Innoactive AR Settings
        self.settings.set("/xrstage/profile/ar/anchorMode", "scene origin")
        self.settings.set("/xrstage/profile/ar/enableCameraOutput", True)
        self.settings.set("/xrstage/profile/ar/cameraOutputPath", "/SessionLayer/XRCam")

    def on_startup(self, ext_id):
        carb.log_info("Extension startup")

        # Access parameters
        self.interface_mode = (
            self.settings.get_as_string("/innoactive/serverextension/interfaceMode")
            or "screen"
        )
        self.usd_to_load = (
            self.settings.get_as_string("/innoactive/serverextension/usdPath")
            or self.default_usd
        )
        # carb.log_info("ANCHOR " + self.settings.get("/xrstage/profile/ar/anchorMode"))

        if self.interface_mode == "vr":
            # Set the resolution multiplier for VR rendering
            self.settings.set("/persistent/xr/profile/vr/system/display", "SteamVR")
            self.settings.set(
                "/persistent/xr/profile/vr/render/resolutionMultiplier", 2.0
            )
            self.settings.set(
                "/persistent/xr/profile/vr/foveation/mode", "warped"
            )  # none / warped / inset
            self.settings.set(
                "/persistent/xr/profile/vr/foveation/warped/resolutionMultiplier", 0.5
            )
            settings.set("/persistent/xr/profile/vr/foveation/warped/insetSize", 0.4)
        elif self.interface_mode == "ar":
            self.settings.set("/xr/cloudxr/version", 4.1)
            self.settings.set("/xr/depth/aov", "GBufferDepth")
            self.settings.set("/xr/simulatedxr/enabled", True)
            self.settings.set("/persistent/renderer/raytracingOmm/enabled", True)
            self.settings.set(
                "/rtx-transient/resourcemanager/enableTextureStreaming", False
            )
            self.settings.set("/xr/ui/enabled", False)
            self.settings.set("/defaults/xr/profile/ar/renderQuality", "off")
            self.settings.set("/defaults/xr/profile/ar/system/display", "CloudXR41")
            self.settings.set("/persistent/xr/profile/ar/render/nearPlane", 0.15)
            self.settings.set(
                "/persistent/rtx/sceneDb/allowDuplicateAhsInvocation", False
            )

        # Get the USD context
        self.usd_context = omni.usd.get_context()

        # Subscribe to stage events
        stage_events = self.usd_context.get_stage_event_stream()
        self._subscriptions.append(
            stage_events.create_subscription_to_pop(
                self._on_stage_event, name="Stage Event Subscription"
            )
        )

        # -- register incoming events/messages
        incoming = {
            # CloudXR data channel
            "CloudXR Action Handler": self._on_execute_action,
        }

        message_bus = omni.kit.app.get_app().get_message_bus_event_stream()
        for event_type, handler in incoming.items():
            carb.log_info(
                f"[innoactive.serverextension] Subscribing for events: {event_type}"
            )
            self._subscriptions.append(
                message_bus.create_subscription_to_pop(handler, name=event_type)
            )

        self._window = ui.Window("Innoactive Server Extension", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")


                def on_load_usd():
                    self.load_usd(usd_file=self.usd_to_load)

                def on_reset_stage():
                    self.load_usd(usd_file=self.empty_stage)
                    carb.log_info("on_reset_stage()")

                def on_load_layout():
                    self.load_layout()
                    carb.log_info("on_load_layout()")

                with ui.VStack():
                    # ui.Button("ConfigVR", clicked_fn=config_vr)
                    ui.Button("Load Layout", clicked_fn=on_load_layout)
                    # ui.Button("Load USD", clicked_fn=on_load_usd)
                    # ui.Button("Reset", clicked_fn=on_reset_stage)

    def on_shutdown(self):
        carb.log_info("Extension shutdown")

        if self._subscriptions:
            self._subscriptions.clear()
