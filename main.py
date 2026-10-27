
from random import randint

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import (
    NumericProperty,
    ReferenceListProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.vector import Vector


class PongBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)

    velocity = ReferenceListProperty(
        velocity_x, velocity_y
    )

    def move(self, dt):
        self.pos = Vector(*self.velocity) * dt + self.pos


class PongPaddle(Widget):
    score = NumericProperty(0)

    def bounce_ball(self, ball):
        if not self.collide_widget(ball):
            return

        # Éviter les rebonds répétés si la balle repart.
        if self.center_x < ball.center_x and ball.velocity_x > 0:
            return

        if self.center_x > ball.center_x and ball.velocity_x < 0:
            return

        if self.height <= 0:
            return

        # Position du point d'impact entre -1 et 1.
        offset = (
            (ball.center_y - self.center_y)
            / (self.height / 2)
        )
        offset = max(-1, min(1, offset))

        # Accélération progressive avec une limite.
        speed = Vector(*ball.velocity).length()
        speed = min(speed * 1.05, 600)

        # L'angle dépend de l'endroit où la balle touche.
        angle = offset * 60

        # Sens horizontal du rebond.
        direction = -1 if ball.center_x < self.center_x else 1

        velocity = Vector(speed, 0).rotate(angle)

        ball.velocity = (
            direction * abs(velocity.x),
            velocity.y,
        )


class PongGame(Widget):
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)

    state = StringProperty("menu")
    winning_score = NumericProperty(10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.menu_widget = None
        self.status_label = None

        # Actualiser le jeu 60 fois par seconde.
        Clock.schedule_interval(self.update, 1 / 60)

    def serve_ball(self, direction=1):
        self.ball.center = self.center

        self.ball.velocity = Vector(
            360 * direction,
            randint(-160, 160),
        )

    def start_game(self, instance=None):
        self.player1.score = 0
        self.player2.score = 0

        self.remove_menu()
        self.state = "playing"

        self.serve_ball(direction=1)

    def pause_game(self, instance=None):
        if self.state != "playing":
            return

        self.state = "paused"
        self.show_menu("PAUSE")

    def resume_game(self, instance=None):
        if self.state != "paused":
            return

        self.remove_menu()
        self.state = "playing"

    def restart_game(self, instance=None):
        self.player1.score = 0
        self.player2.score = 0

        self.remove_menu()
        self.state = "playing"

        self.serve_ball(direction=1)

    def end_game(self, message):
        self.state = "over"

        # Arrêter la balle.
        self.ball.velocity = (0, 0)

        # Afficher le vainqueur et le bouton de revanche.
        self.show_menu(message)

    def show_menu(self, message):
        self.remove_menu()

        self.menu_widget = BoxLayout(
            orientation="vertical",
            spacing=12,
            padding=20,
            size_hint=(None, None),
            size=(400, 300),
            pos=(
                self.center_x - 200,
                self.center_y - 150,
            ),
        )

        self.status_label = Label(
            text=message,
            font_size=30,
            bold=True,
        )
        self.menu_widget.add_widget(self.status_label)

        if self.state == "menu":
            play_button = Button(text="JOUER")
            play_button.bind(on_release=self.start_game)
            self.menu_widget.add_widget(play_button)

        elif self.state == "paused":
            resume_button = Button(text="REPRENDRE")
            resume_button.bind(on_release=self.resume_game)
            self.menu_widget.add_widget(resume_button)

        elif self.state == "over":
            restart_button = Button(text="RECOMMENCER")
            restart_button.bind(on_release=self.restart_game)
            self.menu_widget.add_widget(restart_button)

        # Ajouter un bouton pour revenir au menu principal.
        if self.state != "menu":
            menu_button = Button(text="MENU PRINCIPAL")
            menu_button.bind(on_release=self.back_to_menu)
            self.menu_widget.add_widget(menu_button)

        self.add_widget(self.menu_widget)

    def remove_menu(self):
        if self.menu_widget is not None:
            if self.menu_widget.parent is self:
                self.remove_widget(self.menu_widget)

            self.menu_widget = None
            self.status_label = None

    def back_to_menu(self, instance=None):
        self.ball.velocity = (0, 0)
        self.state = "menu"
        self.show_menu("PONG")

    def update(self, dt):
        if self.state != "playing":
            return

        self.ball.move(dt)

        # Rebond sur le bas et le haut.
        if self.ball.y <= self.y:
            self.ball.y = self.y
            self.ball.velocity_y = abs(self.ball.velocity_y)

        elif self.ball.top >= self.top:
            self.ball.top = self.top
            self.ball.velocity_y = -abs(self.ball.velocity_y)

        # Collision avec les raquettes.
        self.player1.bounce_ball(self.ball)
        self.player2.bounce_ball(self.ball)

        # Le joueur 2 marque si la balle sort à gauche.
        if self.ball.right < self.x:
            self.player2.score += 1

            if self.player2.score >= self.winning_score:
                self.end_game("JOUEUR 2 GAGNE !")
                return

            self.serve_ball(direction=-1)

        # Le joueur 1 marque si la balle sort à droite.
        elif self.ball.x > self.right:
            self.player1.score += 1

            if self.player1.score >= self.winning_score:
                self.end_game("JOUEUR 1 GAGNE !")
                return

            self.serve_ball(direction=1)

    def on_touch_move(self, touch):
        if self.state != "playing":
            return super().on_touch_move(touch)

        # Déplacer la raquette gauche.
        if touch.x < self.x + self.width / 3:
            self.player1.center_y = max(
                self.y + self.player1.height / 2,
                min(
                    touch.y,
                    self.top - self.player1.height / 2,
                ),
            )
            return True

        # Déplacer la raquette droite.
        if touch.x > self.right - self.width / 3:
            self.player2.center_y = max(
                self.y + self.player2.height / 2,
                min(
                    touch.y,
                    self.top - self.player2.height / 2,
                ),
            )
            return True

        return super().on_touch_move(touch)


class PongApp(App):
    def build(self):
        game = PongGame()

        # Le fichier pong.kv définit les raquettes et la balle.
        # On affiche le menu initial une fois l'interface chargée.
        Clock.schedule_once(
            lambda dt: game.show_menu("PONG"),
            0,
        )

        return game


if __name__ == "__main__":
    PongApp().run()
