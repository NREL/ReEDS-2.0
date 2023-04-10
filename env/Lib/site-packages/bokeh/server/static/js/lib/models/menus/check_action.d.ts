import { Action, ActionView } from "./action";
import * as p from "../../core/properties";
export declare class CheckActionView extends ActionView {
    model: CheckAction;
}
export declare namespace CheckAction {
    type Attrs = p.AttrsOf<Props>;
    type Props = Action.Props & {
        checked: p.Property<boolean>;
    };
}
export interface CheckAction extends CheckAction.Attrs {
}
export declare class CheckAction extends Action {
    properties: CheckAction.Props;
    __view_type__: CheckActionView;
    constructor(attrs?: Partial<CheckAction.Attrs>);
}
//# sourceMappingURL=check_action.d.ts.map