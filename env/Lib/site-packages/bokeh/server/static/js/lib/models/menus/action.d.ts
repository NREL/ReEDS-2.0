import { MenuItem, MenuItemView } from "./menu_item";
import { Menu } from "./menu";
import { Icon } from "../ui/icons/icon";
import * as p from "../../core/properties";
export declare class ActionView extends MenuItemView {
    model: Action;
    protected _click(): void;
    render(): void;
}
export declare namespace Action {
    type Attrs = p.AttrsOf<Props>;
    type Props = MenuItem.Props & {
        icon: p.Property<Icon | null>;
        label: p.Property<string>;
        description: p.Property<string | null>;
        menu: p.Property<Menu | null>;
    };
}
export interface Action extends Action.Attrs {
}
export declare class Action extends MenuItem {
    properties: Action.Props;
    __view_type__: ActionView;
    constructor(attrs?: Partial<Action.Attrs>);
}
//# sourceMappingURL=action.d.ts.map