#!/usr/bin/env python
# -*- coding: utf-8 -*-

def esc(id):
    return '\x1b[%dm' % id

# reset colors & styles
ANSI_RESET            = esc(0)

# set style
ANSI_BOLD_ON          = esc(1)
ANSI_ITALICS_ON       = esc(3)
ANSI_UNDERLINE_ON     = esc(4)
ANSI_INVERSE_ON       = esc(7)  # reverses fgcolor/bgcolor
ANSI_STRIKETHROUGH_ON = esc(9)

# unset style
ANSI_BOLD_OFF         = esc(22)
ANSI_ITALICS_OFF      = esc(23)
ANSI_UNDERLINE_OFF    = esc(24)
ANSI_INVERSE_OFF      = esc(27)
ANSI_STRIKETHROUGH_OFF= esc(29)


BLACK    = 0
RED      = 1
GREEN    = 2
YELLOW   = 3
BLUE     = 4
MAGENTA  = 5
CYAN     = 6
WHITE    = 7
DEFAULT  = 9

FGCOLOR_OFFSET = 30
BGCOLOR_OFFSET = 40

# set foreground color
ANSI_FGCOLOR_BLACK    = esc(FGCOLOR_OFFSET + BLACK)
ANSI_FGCOLOR_RED      = esc(FGCOLOR_OFFSET + RED)
ANSI_FGCOLOR_GREEN    = esc(FGCOLOR_OFFSET + GREEN)
ANSI_FGCOLOR_YELLOW   = esc(FGCOLOR_OFFSET + YELLOW)
ANSI_FGCOLOR_BLUE     = esc(FGCOLOR_OFFSET + BLUE)
ANSI_FGCOLOR_MAGENTA  = esc(FGCOLOR_OFFSET + MAGENTA)  # purple
ANSI_FGCOLOR_CYAN     = esc(FGCOLOR_OFFSET + CYAN)
ANSI_FGCOLOR_WHITE    = esc(FGCOLOR_OFFSET + WHITE)
ANSI_FGCOLOR_DEFAULT  = esc(FGCOLOR_OFFSET + DEFAULT)

# set background color
ANSI_BGCOLOR_BLACK    = esc(BGCOLOR_OFFSET + BLACK)
ANSI_BGCOLOR_RED      = esc(BGCOLOR_OFFSET + RED)
ANSI_BGCOLOR_GREEN    = esc(BGCOLOR_OFFSET + GREEN)
ANSI_BGCOLOR_YELLOW   = esc(BGCOLOR_OFFSET + YELLOW)
ANSI_BGCOLOR_BLUE     = esc(BGCOLOR_OFFSET + BLUE)
ANSI_BGCOLOR_MAGENTA  = esc(BGCOLOR_OFFSET + MAGENTA)
ANSI_BGCOLOR_CYAN     = esc(BGCOLOR_OFFSET + CYAN)
ANSI_BGCOLOR_WHITE    = esc(BGCOLOR_OFFSET + WHITE)
ANSI_BGCOLOR_DEFAULT  = esc(BGCOLOR_OFFSET + DEFAULT)

def bold(text, color=ANSI_FGCOLOR_DEFAULT):
    if color == ANSI_FGCOLOR_DEFAULT:
        return ANSI_BOLD_ON + text + ANSI_BOLD_OFF
    else:
        return ANSI_BOLD_ON + fgcolor(color, text) + ANSI_BOLD_OFF

def italics(text):
    return ANSI_ITALICS_ON + text + ANSI_ITALICS_OFF

def underline(text):
    return ANSI_UNDERLINE_ON + text + ANSI_UNDERLINE_OFF

def inverse(text):
    return ANSI_INVERSE_ON + text + ANSI_INVERSE_OFF

def striketthrough(text):
    return ANSI_STRIKETHROUGH_ON + text + ANSI_STRIKETHROUGH_OFF

def fgcolor(color, text):
    return esc(FGCOLOR_OFFSET + color) + text + esc(FGCOLOR_OFFSET + DEFAULT)

def bgcolor(color, text):
    return esc(BGCOLOR_OFFSET + color) + text + esc(BGCOLOR_OFFSET + DEFAULT)
