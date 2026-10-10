from short_video_generator.contracts import (
    EditorialBrief,
    SemanticScenePlan,
    SemanticStoryPlan,
    VisualConcept,
)


class DeterministicStoryPlanner:
    version = "semantic-story-plan-v1"

    def create(self, brief: EditorialBrief) -> SemanticStoryPlan:
        topic = brief.topic
        claim = brief.key_points[0]
        scenes = (
            SemanticScenePlan(
                order=1,
                role="hook",
                communicative_goal=f"Create curiosity about {topic} without revealing the answer.",
                new_information=f"There is a concrete question hidden inside {topic}.",
                relation_to_previous="introduces",
                viewer_learns=(
                    f"The viewer wants to understand the practical question behind {topic}."
                ),
                narration=f"Why does {topic} work differently than most people expect?",
                visual_concept=VisualConcept(
                    subject=f"person noticing a problem related to {topic}",
                    observable_action="pauses and looks at the unexpected result",
                    environment="everyday setting",
                    supporting_objects=("phone", "notebook"),
                    visual_goal="make the opening question visible",
                ),
            ),
            SemanticScenePlan(
                order=2,
                role="context",
                communicative_goal=f"Give the minimum context needed to understand {topic}.",
                new_information=(
                    f"The outcome depends on how people interact with {topic}, "
                    "not only on the label itself."
                ),
                relation_to_previous="clarifies",
                viewer_learns="The viewer can distinguish the situation from the opening question.",
                narration=f"The important detail is the moment when someone actually uses {topic}.",
                visual_concept=VisualConcept(
                    subject=f"person preparing to use {topic}",
                    observable_action="sets up the object before starting",
                    environment="home or desk",
                    supporting_objects=("device", "notes"),
                    visual_goal="establish the real-world situation",
                ),
            ),
            SemanticScenePlan(
                order=3,
                role="mechanism",
                communicative_goal=f"Explain the mechanism behind {topic}.",
                new_information=f"The mechanism behind the claim is: {claim}",
                relation_to_previous="explains",
                viewer_learns=f"The viewer understands why {topic} produces its effect.",
                narration=(
                    "That happens because "
                    f"{claim[0].lower() + claim[1:] if claim else claim}"
                ),
                visual_concept=VisualConcept(
                    subject=f"person performing the key step in {topic}",
                    observable_action="moves from the initial state to the resulting state",
                    environment="clear explanatory setting",
                    supporting_objects=("before card", "after card"),
                    visual_goal="show the mechanism as an observable action",
                ),
            ),
            SemanticScenePlan(
                order=4,
                role="example",
                communicative_goal="Turn the mechanism into a concrete everyday example.",
                new_information=(
                    "A single practical example shows when the mechanism changes the result."
                ),
                relation_to_previous="exemplifies",
                viewer_learns="The viewer can recognize the mechanism in a real situation.",
                narration=(
                    f"You can see it clearly when someone applies {topic} to one "
                    "specific situation."
                ),
                visual_concept=VisualConcept(
                    subject=f"person applying {topic} to one concrete task",
                    observable_action="tries the step, checks the result, and adjusts",
                    environment="real-world workspace",
                    supporting_objects=("checklist", "timer", "result"),
                    visual_goal="make the abstract explanation recordable",
                ),
            ),
            SemanticScenePlan(
                order=5,
                role="payoff",
                communicative_goal="Synthesize the explanation into a useful takeaway.",
                new_information=(
                    "The useful decision is to apply the mechanism deliberately "
                    "instead of relying on appearances."
                ),
                relation_to_previous="applies",
                viewer_learns="The viewer knows what to do differently after the explanation.",
                narration=(
                    f"So the practical takeaway is simple: use the mechanism behind {topic}, "
                    "not just its surface result."
                ),
                visual_concept=VisualConcept(
                    subject=f"person choosing the effective action for {topic}",
                    observable_action="switches from the ineffective option to the useful one",
                    environment="everyday decision point",
                    supporting_objects=("two options", "finished result"),
                    visual_goal="make the payoff visibly actionable",
                ),
            ),
        )
        return SemanticStoryPlan(topic=topic, central_claim=claim, scenes=scenes)
