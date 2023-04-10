import { ActionTool, ActionToolView } from "./action_tool";
import { CallbackLike0 } from "../../callbacks/callback";
import * as p from "../../../core/properties";
export declare class CustomActionView extends ActionToolView {
    model: CustomAction;
    doit(): void;
}
export declare namespace CustomAction {
    type Attrs = p.AttrsOf<Props>;
    type Props = ActionTool.Props & {
        callback: p.Property<CallbackLike0<CustomAction> | null>;
    };
}
export interface CustomAction extends CustomAction.Attrs {
}
export declare class CustomAction extends ActionTool {
    properties: CustomAction.Props;
    __view_type__: CustomActionView;
    constructor(attrs?: Partial<CustomAction.Attrs>);
    tool_name: string;
    tool_icon: string;
}
//# sourceMappingURL=custom_action.d.ts.map