class Container:
    def __init__(self, pos_x_rel, pos_y_rel, W_rel, H_rel, parent):
        self.pos_x_rel  = pos_x_rel
        self.pos_y_rel  = pos_y_rel
        self.W_rel      = W_rel
        self.H_rel      = H_rel
        self.parent     = parent
        self.containers = []
        self.leaves     = []

    @property
    def is_last_level(self):
        return len(self.containers) == 0
    
    @property
    def size(self):
        return (self.W_px, self.H_px)
    
    @property
    def W_px(self):
        return self.W_rel * self.parent.W_px
    
    @property
    def H_px(self):
        return self.H_rel * self.parent.H_px
    
    def add_container(self, container):
        self.containers.append(container)

    def add_leaf(self, leaf):
        self.leaves.append(leaf)
