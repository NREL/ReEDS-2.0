import { AbstractButton, AbstractButtonView } from "./abstract_button";
import { CallbackLike1 } from "../callbacks/callback";
import { StyleSheetLike } from "../../core/dom";
import * as p from "../../core/properties";
export declare class DropdownView extends AbstractButtonView {
    model: Dropdown;
    protected _open: boolean;
    protected menu: HTMLElement;
    stylesheets(): StyleSheetLike[];
    render(): void;
    protected _show_menu(): void;
    protected _hide_menu(): void;
    protected _toggle_menu(): void;
    click(): void;
    protected _item_click(i: number): void;
}
export declare namespace Dropdown {
    type Attrs = p.AttrsOf<Props>;
    type Props = AbstractButton.Props & {
        split: p.Property<boolean>;
        menu: p.Property<(string | [string, string | CallbackLike1<Dropdown, {
            index: number;
        }>] | null)[]>;
    };
}
export interface Dropdown extends Dropdown.Attrs {
}
export declare class Dropdown extends AbstractButton {
    properties: Dropdown.Props;
    __view_type__: DropdownView;
    constructor(attrs?: Partial<Dropdown.Attrs>);
    get is_split(): boolean;
}
//# sourceMappingURL=dropdown.d.ts.map