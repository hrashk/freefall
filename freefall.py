from matplotlib.patches import Arc
from matplotlib.path import Path
import numpy as np
from matplotlib import animation
from matplotlib import pyplot as plt


v0 = 10
g = 10


def x_t(t, angle):
    return v0 * np.cos(np.deg2rad(angle)) * t


def y_t(t, angle):
    return v0 * np.sin(np.deg2rad(angle)) * t - g * t * t / 2


def envelope_y(x):
    return -g * x ** 2 / (2 * v0 ** 2) + v0 ** 2 / (2 * g)


def mix_in(instance, clazz):
    """Adds clazz to instance's base classes
    Based on http://stackoverflow.com/a/8545287/1622347"""
    instance.__class__ = type(
        '{}_extended_with_{}'.format(instance.__class__.__name__, clazz.__name__),
        (instance.__class__, clazz),
        {}
    )
    clazz.__init__(instance)


class TimeMixin():
    def __init__(self):
        self.time = 0
        super().__init__()

    def reset_time(self):
        self.time = 0


class AngleMixin():
    def __init__(self):
        self.angle = 0
        super().__init__()

    def set_angle(self, angle):
        self.angle = angle


class DynamicBeeMixin(AngleMixin, TimeMixin):
    def __init__(self):
        self.set_marker('*')
        self.set_markersize(4)
        super().__init__()

    def tick(self, dt):
        self.time += dt
        t = np.array([self.time])
        self.set_data(x_t(t, self.angle), y_t(t, self.angle))


class DynamicTrailMixin(AngleMixin, TimeMixin):
    def __init__(self):
        self.set_linestyle('-')
        self.set_linewidth(0.3)
        self.set_alpha(0.3)
        super().__init__()

    def tick(self, dt):
        self.time += dt
        t = np.linspace(0, self.time)
        self.set_data(x_t(t, self.angle), y_t(t, self.angle))


class TrailEnvelopeMixin():
    def __init__(self):
        self.set_linestyle('-')
        self.set_linewidth(1)
        self.set_alpha(0.5)
        self.x1 = self.x2 = 0
        super().__init__()

    def tick(self, dt):
        self.x1 -= 55 * dt
        x = np.linspace(self.x1, self.x2)
        self.set_data(x, envelope_y(x))


class TurnBasedMixin():
    def __init__(self):
        self.next_artists = ()
        self.is_my_turn = False
        self.set_visible(False)
        super().__init__()

    def set_next_artists(self, artists):
        self.next_artists = artists

    def set_my_turn(self):
        self.is_my_turn = True

    def tick(self, dt):
        if not self.is_my_turn:
            return
        if not self.get_visible():
            self.set_visible(True)
        else:
            self.is_my_turn = False
            for artist in self.next_artists:
                artist.set_my_turn()


class TrailMixin(TurnBasedMixin):
    def __init__(self):
        self.set_linestyle('-')
        self.set_linewidth(0.3)
        self.set_alpha(0.3)
        super().__init__()

    def set_angle(self, angle, t1=0, t2=3):
        t = np.linspace(t1, t2)
        self.set_data(x_t(t, angle), y_t(t, angle))


class VertexMixin(TurnBasedMixin):
    def __init__(self):
        self.set_marker('o')
        self.set_markersize(4)
        super().__init__()

    def set_angle(self, angle):
        angle = np.deg2rad(angle)
        y = v0 ** 2 * np.sin(angle) ** 2 / (2 * g)
        x = v0 ** 2 * np.sin(2 * angle) / (2 * g)
        self.set_data(np.array([x]), np.array([y]))


class FocusMixin(TurnBasedMixin):
    def __init__(self):
        self.set_marker('o')
        self.set_markersize(4)
        super().__init__()

    def set_angle(self, angle):
        angle = np.deg2rad(angle)
        x = v0 ** 2 * np.sin(2 * angle) / (2 * g)
        y = -v0 ** 2 * np.cos(2 * angle) / (2 * g)
        self.set_data(np.array([x]), np.array([y]))


class DynamicArc(Arc):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_alpha(0.5)

    def set_theta2(self, angle):
        self.theta2 = angle
        self._path = Path.arc(self.theta1, self.theta2)

    def tick(self, dt):
        self.set_theta2(self.theta2)


class DynamicTangentMixin(AngleMixin):
    def __init__(self):
        self.set_alpha(0.5)
        super().__init__()

    def tick(self, dt):
        length = v0 ** 2 / (4 * g)
        angle = np.deg2rad(self.angle)
        tan_x = length * np.cos(angle)
        tan_y = length * np.sin(angle)
        self.set_data([0, tan_x], [0, tan_y])


class DynamicLabelMixin(AngleMixin):
    def __init__(self):
        self.set_alpha(0.5)
        super().__init__()

    def tick(self, dt):
        self.set_text("${}^o$".format(self.angle))


def setup_axes(width, height, xlim, ylim):
    fig = plt.figure(figsize=(width, height))
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0.01)
    ax = fig.gca()
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect('equal')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_visible(False)
    ax.set_color_cycle(['k'])
    return fig, ax


def create_artists_anime1(ax, angle):
    trail, = ax.plot([], [])
    mix_in(trail, DynamicTrailMixin)
    trail.set_angle(angle)

    bee, = ax.plot(np.array([0]), np.array([0]))
    mix_in(bee, DynamicBeeMixin)
    bee.set_angle(angle)

    tangent, = ax.plot([], [])
    mix_in(tangent, DynamicTangentMixin)
    tangent.set_angle(angle)

    label = ax.text(1, 0.5, "", fontdict={'size': 11})
    mix_in(label, DynamicLabelMixin)
    label.set_angle(angle)

    arc = DynamicArc(xy=(0, 0), width=2, height=2, theta2=angle)
    ax.add_patch(arc)
    return trail, bee, tangent, label, arc


def create_fading_envelope(ax, x1, x2):
    trail, = ax.plot([], [])
    mix_in(trail, TrailEnvelopeMixin)
    trail.x1 = x1
    trail.x2 = x2
    return trail


def angular_artists(ax, angles, artist_mixin):
    artists = []
    for angle in angles:
        artist, = ax.plot([], [])
        mix_in(artist, artist_mixin)
        artist.set_angle(angle)
        artists.append(artist)
    return artists


def trails_and_features(ax, angle_step, feature_mixin):
    """A feature is defined by its mixin class.
     It could be a vertex, a focus, a tip, a directrix, etc."""
    angles = tuple(range(0, 180, angle_step))
    trails = angular_artists(ax, angles, TrailMixin)
    features = angular_artists(ax, angles, feature_mixin)
    return sum(zip(trails, features), ())


def pair_up_artists(artists):
    """This method makes artists show up in pairs in the animation."""
    if len(artists) < 2:
        return
    for idx in range(0, len(artists) - 2, 2):
        artists[idx].set_next_artists([artists[idx + 2]])
        artists[idx + 1].set_next_artists([artists[idx + 3]])
    if len(artists) > 2:
        artists[-2].set_next_artists([artists[0]])  # loop the last trail to the first one
        artists[-1].set_next_artists([artists[1]])  # same thing for their features
    artists[0].set_my_turn()  # start from the first trail
    artists[1].set_my_turn()  # and feature
    return artists


def sequence_artists(artists):
    """This method makes artists show up in sequence in the animation."""
    for idx in range(len(artists) - 1):
        artists[idx].set_next_artists([artists[idx + 1]])
    artists[-1].set_next_artists([artists[0]])  # loop
    artists[0].set_my_turn()  # start from the first trail
    return artists


def trails_interleaved_with_vertices(ax, angle_step):
    return sequence_artists(trails_and_features(ax, angle_step, feature_mixin=VertexMixin))


def trails_together_with_vertices(ax, angle_step):
    return pair_up_artists(trails_and_features(ax, angle_step, feature_mixin=VertexMixin))


def trails_interleaved_with_foci(ax, angle_step):
    return sequence_artists(trails_and_features(ax, angle_step, feature_mixin=FocusMixin))


def animate_time(i, *artists):
    for artist in artists:
        artist.tick(0.02)
    return artists


def anime_freefall():
    fig, ax = setup_axes(width=4.5, height=1.2, xlim=(-0.1, 10.1), ylim=(-0.1, 5.1))
    artists = create_artists_anime1(ax, angle=65)
    anim = animation.FuncAnimation(fig, animate_time, init_func=lambda: artists, save_count=90,
                                   fargs=artists, interval=10, blit=True)
    anim.save('anime1.mp4', fps=20)


def anime_firework():
    fig, ax = setup_axes(width=3.5, height=2.4, xlim=(-20.1, 20.1), ylim=(-30.1, 5.5))
    angles = tuple(range(0, 360, 15))
    bees = angular_artists(ax, angles, DynamicBeeMixin)
    trails = angular_artists(ax, angles, DynamicTrailMixin)
    artists = bees + trails
    anim = animation.FuncAnimation(fig, animate_time, init_func=lambda: artists, save_count=80,
                                   fargs=artists, interval=10, blit=True)
    anim.save('anime2.mp4', fps=20)


def anime_vertices():
    fig, ax = setup_axes(width=4.5, height=1.2, xlim=(-10.1, 10.1), ylim=(-0.1, 5.1))
    artists = trails_interleaved_with_vertices(ax, 10)
    anim = animation.FuncAnimation(fig, animate_time, init_func=lambda: artists,
                                   fargs=artists, save_count=36, interval=10, blit=True)
    anim.save('anime3.mp4', fps=1)


def anime_foci():
    fig, ax = setup_axes(width=4.5, height=1.2, xlim=(-10.1, 10.1), ylim=(-5.1, 5.4))
    artists = trails_interleaved_with_foci(ax, 10)
    anim = animation.FuncAnimation(fig, animate_time, init_func=lambda: artists,
                                   save_count=36, fargs=artists, interval=10, blit=True)
    anim.save('anime4.mp4', fps=1)


def anime_intro():
    fig, ax = setup_axes(width=4.5, height=1.2, xlim=(-10.1, 10.1), ylim=(-0.1, 5.1))
    angle_step = 10
    artists = trails_together_with_vertices(ax, angle_step)
    envelope = create_fading_envelope(ax, 10, 10)
    artists += (envelope,)
    anim = animation.FuncAnimation(fig, animate_time, interval=10, save_count=18,
                                   init_func=lambda: artists, fargs=artists, blit=True)
    anim.save('intro.mp4', fps=1)


if __name__ == '__main__':
    anime_freefall()
    anime_firework()
    anime_vertices()
    anime_foci()
    anime_intro()
