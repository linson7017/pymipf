from trame.app import get_server
from trame.ui.vuetify import VAppLayout
from trame.widgets import vuetify


server = get_server(client_type="vue2")
state = server.state
state.value = 1


@state.change("files")
def value_changed():
    print("state value changed:", state.value)


class TestUI:
    def __init__(self, state):
        self.ui = vuetify.VBtn(
            "Test",
            click=self.call_test,
        )

    def __call__(self, *args, **kwds):
        return self.ui

    def call_test(self):
        print("test")
        state.value += 1


with VAppLayout(server):
    TestUI(server.state)


if __name__ == "__main__":
    server.start()
