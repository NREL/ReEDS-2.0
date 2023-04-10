import * as p from "../../core/properties";
import { ButtonType } from "../../core/enums";
import { StyleSheetLike } from "../../core/dom";
import { IterViews } from "../../core/build_views";
import { Control, ControlView } from "./control";
import { Icon, IconView } from "../ui/icons/icon";
export declare abstract class AbstractButtonView extends ControlView {
    model: AbstractButton;
    protected icon_view?: IconView;
    button_el: HTMLButtonElement;
    protected group_el: HTMLElement;
    controls(): Generator<HTMLButtonElement, void, unknown>;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    connect_signals(): void;
    remove(): void;
    stylesheets(): StyleSheetLike[];
    _render_button(...children: (string | HTMLElement)[]): HTMLButtonElement;
    render(): void;
    click(): void;
}
export declare namespace AbstractButton {
    type Attrs = p.AttrsOf<Props>;
    type Props = Control.Props & {
        label: p.Property<string>;
        icon: p.Property<Icon | null>;
        button_type: p.Property<ButtonType>;
    };
}
export interface AbstractButton extends AbstractButton.Attrs {
}
export declare abstract class AbstractButton extends Control {
    properties: AbstractButton.Props;
    __view_type__: AbstractButtonView;
    constructor(attrs?: Partial<AbstractButton.Attrs>);
}
//# sourceMappingURL=abstract_button.d.ts.map