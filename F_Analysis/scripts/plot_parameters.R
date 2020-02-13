# plot parameters

# --------------------------------------------------- |
# plot theme ----
# --------------------------------------------------- |

# size of text in plots
large.text.size = 10.5
small.text.size = 9
text.plot = 11

# plot theme
plot_theme = 
  theme(legend.key = element_rect(color = "grey80", size = 0.8), 
        legend.key.size = grid::unit(1.0, "lines"),
        legend.text = element_text(size = small.text.size, margin = margin(l = 5)), 
        legend.title = element_blank(), 
        axis.text = element_text(size = small.text.size), 
        axis.text.x = element_text(size = small.text.size),
        axis.title = element_text(size = large.text.size, face = "bold"),
        axis.title.x= element_text(size=large.text.size, vjust = 1.2, face = "bold"),
        axis.title.y = element_text(size=large.text.size, vjust = 1.2, face = "bold"),
        strip.text = element_text(size=small.text.size),
        panel.spacing = unit(0.5, "lines"))

