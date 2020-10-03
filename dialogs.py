from ptypes import Point, Rect
import config
import curses
import os


class Dialog(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rect = None

    def draw(self, app):
        cx = int(app.width / 2)
        cy = int(app.height / 2)
        y = int(cy - self.height / 2)
        x = int(cx - self.width / 2)
        self.rect = Rect(x, y, x + self.width, y + self.height)
        app.draw_frame(self.rect, 4)
        app.fill_rect(Rect(self.rect).inflate(-1), ' ', 4)


class MessageBox(Dialog):
    def __init__(self, prompt):
        super(MessageBox, self).__init__(60, 8)
        self.prompt = prompt
        self.actions = {}

    def add_key(self, key, action):
        self.actions[key.lower()] = action
        self.actions[key.upper()] = action

    def process_key(self, key):
        if key in self.actions:
            return self.actions.get(key)
        return None

    def draw(self, app):
        super(MessageBox, self).draw(app)
        app.move(Point(self.rect.tl.x + 4, self.rect.tl.y + 4))
        app.write(self.prompt, 4)


class AboutDialog(Dialog):
    def __init__(self):
        super(AboutDialog, self).__init__(40, 20)

    def draw(self, app):
        super(AboutDialog, self).draw(app)
        pos = self.rect.tl + Point(4, 3)
        lines = ('Yet Another Text EDitor',
                 '',
                 'A terminal based text editor, ',
                 'inspired by a wish to have',
                 'an editor with default visual',
                 'and key bindings that resemble',
                 'typical GUI based editors.',
                 '',
                 'https://github.com/amirgeva/yated'
                 )
        for line in lines:
            app.move(pos)
            app.write(line, 4)
            pos += (0, 1)

    def process_key(self, key):
        return True


class FileDialog(Dialog):
    def __init__(self, action):
        super(FileDialog, self).__init__(60, 20)
        self.dir = os.getcwd()
        self.browse_mode = True
        self.edit_text = ''
        self.editpos = None
        self.ofs = 0
        self.cur = 0
        self.items = []
        self.fill_items()
        self.action = action

    def fill_items(self):
        files = os.listdir(self.dir)
        for i in range(0, len(files)):
            name = files[i]
            path = os.path.join(self.dir, name)
            if os.path.isdir(path):
                name = name + '/'
            files[i] = name
        files.insert(0, '../')
        self.items = files

    def draw(self, app):
        super(FileDialog, self).draw(app)
        pos = self.rect.tl + Point(1, 1)
        app.move(pos)
        app.write(self.dir + '/', 1)
        self.editpos = pos + (len(self.dir) + 1, 0)
        pos += (2, 1)
        for i in range(0, 17):
            c = 4
            idx = i + self.ofs
            app.move(pos)
            if idx < len(self.items):
                attr = 0
                if self.cur == idx:
                    c = 1
                s = self.items[idx]
                if len(s) > 50:
                    s = s[0:50]
                if len(s) < 50:
                    s = s + ' ' * (50 - len(s))
                app.write(s, c, attr)
            else:
                app.write(' ' * 50, c)
            pos += (0, 1)
        if not self.browse_mode:
            app.move(self.editpos)
            app.write(self.edit_text, 1)

    def process_key(self, key):
        if self.browse_mode:
            if key == chr(9):  # tab
                self.browse_mode = False
            if key == 'KEY_DOWN':
                self.cur = (self.cur + 1) % len(self.items)
            if key == 'KEY_UP':
                self.cur = (self.cur - 1) % len(self.items)
            if key == 'KEY_END':
                self.cur = len(self.items) - 1
            if key == 'KEY_HOME':
                self.cur = 0
            if key == 'KEY_PPAGE':
                self.cur = (self.cur - 17) % len(self.items)
            if key == 'KEY_NPAGE':
                self.cur = (self.cur + 17) % len(self.items)
            if key == chr(10):  # Enter
                name = self.items[self.cur]
                path = os.path.abspath(os.path.join(self.dir, name))
                if name.endswith('/'):
                    self.dir = path
                    self.fill_items()
                else:
                    return lambda: self.action(path)
            if self.cur < self.ofs or self.cur >= (self.ofs + 17):
                self.ofs = self.cur - 8
                if self.ofs < 0:
                    self.ofs = 0
        else:
            if key == chr(9):  # tab
                self.browse_mode = True
            if len(key) == 1 and 32 < ord(key) < 128:
                self.edit_text += key
            if key == 'KEY_BACKSPACE' and len(self.edit_text) > 0:
                self.edit_text = self.edit_text[0:-1]
            if key == chr(10):
                path = os.path.abspath(os.path.join(self.dir, self.edit_text))
                return lambda: self.action(path)
        return None


class FormWidget(object):
    def __init__(self, pos):
        self.text = ''
        self.pos = pos
        self.tabstop = False


class FormCheckbox(FormWidget):
    def __init__(self, pos, state=False):
        super(FormCheckbox, self).__init__(pos)
        self.tabstop = True
        self.state = state

    def details(self):
        return self.state

    def draw(self, app, tl):
        app.move(self.pos + tl - Point(1, 0))
        mark = 'X' if self.state else ' '
        app.write('[{}]'.format(mark), 4)
        app.move(self.pos + tl)

    def process_key(self, key):
        if key == ' ':
            self.state = not self.state


class FormLabel(FormWidget):
    def __init__(self, pos, text):
        super(FormLabel, self).__init__(pos)
        self.text = text
        self.color = 4
        self.pad = 0

    def draw(self, app, tl):
        app.move(self.pos + tl)
        app.write(self.text, self.color)
        if self.pad > len(self.text):
            app.write(' ' * (self.pad - len(self.text)), self.color)


class FormEdit(FormLabel):
    def __init__(self, pos, text, maxlen):
        super(FormEdit, self).__init__(pos, text)
        self.tabstop = True
        self.color = 1
        self.maxlen = maxlen
        self.pad = maxlen

    def details(self):
        return self.text

    def draw(self, app, tl):
        super(FormEdit, self).draw(app, tl)
        app.move(self.pos + tl + Point(len(self.text), 0))

    def process_key(self, key):
        if len(key) == 1 and 32 <= ord(key[0]) < 128:
            self.text = self.text + key
        if key == 'KEY_BACKSPACE' and len(self.text) > 0:
            self.text = self.text[0:-1]


class FormDialog(Dialog):
    def __init__(self, w, h):
        super(FormDialog, self).__init__(w, h)
        self.widgets = []
        self.named_widgets = {}
        self.cur = None

    def details(self, vals=None):
        if vals is None:
            vals = []
        res = {}
        for val in vals:
            res[val[0]] = val[1]
        for name in self.named_widgets:
            res[name] = self.named_widgets.get(name).details()
        return res

    def add_widget(self, name, widget):
        if isinstance(widget, FormWidget):
            self.widgets.append(widget)
            if name:
                self.named_widgets[name] = widget
            if self.cur is None and widget.tabstop:
                self.cur = len(self.widgets) - 1

    def draw(self, app):
        super(FormDialog, self).draw(app)
        for i in range(0, len(self.widgets)):
            widget = self.widgets[i]
            if self.cur != i:
                widget.draw(app, self.rect.tl)
        if self.cur is not None:
            self.widgets[self.cur].draw(app, self.rect.tl)

    def process_key(self, key):
        if key == chr(9):  # tab
            while True:
                self.cur = (self.cur + 1) % len(self.widgets)
                if self.widgets[self.cur].tabstop:
                    break
        if key == 'KEY_BTAB':  # back-tab
            while True:
                self.cur = (self.cur - 1) % len(self.widgets)
                if self.widgets[self.cur].tabstop:
                    break
        if self.cur is not None:
            self.widgets[self.cur].process_key(key)
        return None


class FindReplaceDialog(FormDialog):
    def __init__(self, find_action, replace_action):
        super(FindReplaceDialog, self).__init__(60, 20)
        self.find_action = find_action
        self.replace_action = replace_action
        self.add_widget('', FormLabel(Point(2, 2), 'Find:'))
        self.add_widget('find', FormEdit(Point(12, 2), config.get('find_text'), 40))
        self.add_widget('', FormLabel(Point(2, 3), 'Replace:'))
        self.add_widget('replace', FormEdit(Point(12, 3), config.get('find_replace'), 40))
        self.add_widget('case', FormCheckbox(Point(4, 5), config.getbool('find_case')))
        self.add_widget('', FormLabel(Point(8, 5), 'Case Sensitive'))
        self.add_widget('regex', FormCheckbox(Point(4, 6), config.getbool('find_regex')))
        self.add_widget('', FormLabel(Point(8, 6), 'Regular Expressions'))
        self.add_widget('word', FormCheckbox(Point(4, 7), config.getbool('find_word')))
        self.add_widget('', FormLabel(Point(8, 7), 'Whole Word'))
        #
        self.add_widget('', FormLabel(Point(2, 16), 'Enter to find,  Ctrl+R to replace,  Ctrl+A to replace all'))

    def process_key(self, key):
        props = [('all', False), ('first', True)]
        if key == chr(18):  # Ctrl+R
            return lambda: self.replace_action(self.details(props))
        if key == chr(1):  # Ctrl+A
            props[0] = 'all', True
            return lambda: self.replace_action(self.details(props))
        if key == chr(10):  # Enter
            return lambda: self.find_action(self.details(props))
        return super(FindReplaceDialog, self).process_key(key)


class ColorConfigDialog(Dialog):
    def __init__(self):
        super(ColorConfigDialog, self).__init__(60, 15)
        self.cur = 1

    def draw(self, app):
        super(ColorConfigDialog, self).draw(app)
        pos = self.rect.tl + Point(2, 2)
        for i in range(1, 8):
            app.move(pos)
            attr = 0
            c = 4
            if i == self.cur:
                c = 1
            app.write(f'Color {i}  ', c, attr)
            app.write('ABC', i)
            pos += (0, 1)
        pos += Point(8, 1)
        app.move(pos)
        app.write('Use left/right pgup/pgdn to change colors', 4)
        app.move(pos + (0, 1))
        app.write('Esc when done', 4)

    def process_key(self, key):
        if key == 'KEY_DOWN':
            self.cur = 1 + (self.cur % 7)
        if key == 'KEY_UP':
            self.cur = 1 + ((self.cur - 2) % 7)

        fg = config.getint('fg{}'.format(self.cur))
        bg = config.getint('bg{}'.format(self.cur))
        if key == 'KEY_LEFT':
            fg = (fg - 1) % 8
        if key == 'KEY_RIGHT':
            fg = (fg + 1) % 8
        if key == 'KEY_PPAGE':
            bg = (bg - 1) % 8
        if key == 'KEY_NPAGE':
            bg = (bg + 1) % 8
        config.set('fg{}'.format(self.cur), fg)
        config.set('bg{}'.format(self.cur), bg)
        curses.init_pair(self.cur, fg, bg)
        return None


class EditorOptionsDialog(FormDialog):
    def __init__(self, action):
        super(EditorOptionsDialog, self).__init__(60, 20)
        self.action = action
        self.add_widget('', FormLabel(Point(2, 2), 'Tab Size:'))
        self.add_widget('tabsize', FormEdit(Point(16, 2), config.get('tabsize', '4'), 2))
        self.add_widget('', FormLabel(Point(2, 16), 'Enter to save,  Esc to cancel'))

    def process_key(self, key):
        super(EditorOptionsDialog, self).process_key(key)
        if key == chr(10):
            return lambda: self.action(self.details())
        return None
