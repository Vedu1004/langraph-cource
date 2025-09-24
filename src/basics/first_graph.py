import os
from typing import TypedDict, Literal
from langgraph.graph import StateGraph,END 
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage,SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv


load_dotenv()
os.environ["OPENAI_API_KEY"] ="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"
llm = ChatOpenAI(
    model = "gpt-3.5-turbo",
    temperature = 0.5
)

class jokeState(TypedDict):
    topic:str
    joke:str
    rating:str
    feedback:str
    joke_history:list
    attempt_count:int

def generate_joke_withllm(state:jokeState)-> dict:
    messages = [
        SystemMessage(content="You are a comedian who tells short, witty jokes."),
        HumanMessage(content=f"Tell me a short, funny joke about {state['topic']}. Just the joke, no explanation.")
    ]
    response = llm.invoke(messages)
    joke = response.content
    return {"joke":joke}

def rate_joke_with_llm(state:jokeState)->dict:
    message = [
        SystemMessage(content="you are a critic that rate the jokes"),
        HumanMessage(content=f"""
        Rate this joke from 1-10 and provide feedback.

        Joke: {state['joke']}

        You MUST format your response exactly like this:
        Rating: [number]/10
        Feedback: [one sentence]
        """)
    ]
    response = llm.invoke(message)
     # Fixed parsing logic:
    response_text = response.content
    rating = "6/10"  # default
    
    # Case-insensitive search for rating
    if "Rating:" in response_text or "rating:" in response_text.lower():
        try:
            # Split case-insensitively 
            parts = response_text.replace("rating:", "Rating:").split("Rating:")
            if len(parts) > 1:
                rating_line = parts[1].split("\n")[0]
                rating = rating_line.strip()
        except:
            pass
    
    return {
        "rating": rating,
        "feedback": response_text
    }

def improve_joke_withllm(state:jokeState)->dict:
    joke = state['joke']
    message = [
        SystemMessage(content = "you are a comedian who improvise the jokes"),
        HumanMessage(content =f"""
            Original joke: {state['joke']}
        
            Feedback: {state['feedback']}
            
           create a much beeter joke or the improvised version of teh joke that adresses the feedback, just give teh joske nothing else.
        """)
    ]
    response =llm.invoke(message)
    improvised_joke = response.content
    return {"joke":improvised_joke}

def should_improve(state:jokeState)->Literal["improve", "done"]:
    try:
        rating_num = int(state["rating"].split("/")[0])
        
        if rating_num < 7:
            print(f"   ↩️  Rating {rating_num} is low, let's improve it!")
            return "improve"
        else:
            print(f"   ✅ Rating {rating_num} is good enough!")
            return "done"
    except:
        return "done"

def create_jokegraph():
    checkpointer = MemorySaver()
    graph = StateGraph(jokeState)
    graph.add_node("joke_generator",generate_joke_withllm)
    graph.add_node("check_duplicate",check_duplicate)
    graph.add_node("joke_rating",rate_joke_with_llm)
    graph.add_node("joke_improver",improve_joke_withllm)
    graph.set_entry_point("joke_generator")
    graph.add_edge("joke_generator","check_duplicate")
    graph.add_edge("check_duplicate","joke_rating")

    graph.add_conditional_edges (
        "joke_rating",
        should_improve,{
            "improve":"joke_improver",
            "done":END
        }
    )
    graph.add_edge("joke_improver","joke_rating")

    app = graph.compile(checkpointer=checkpointer)
    # print("\n🔍 Graph Structure:")
    # print("Nodes:", list(app.get_graph().nodes.keys()))
    # print("Edges:", app.get_graph().edges)

    return app

def check_duplicate(state: jokeState)->dict:
    current_joke = state['joke']
    history= state.get('joke_history',[])
    if current_joke in history:
        print("duplicate joke detected")
        return {"rating":"1/10"}
    else:
        history.append(current_joke)
        attempt_count = state.get("attempt_count",0) +1
        return {"joke_history":history,"attempt_count" :attempt_count}


if __name__ == "__main__":
    print("langraph joke generator 2 node ----")
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY in your .env file!")
        exit(1)
    
    app = create_jokegraph()

    topic = input("\nEnter a topic for the joke: ") or "programming"

    initial_state = {
        "topic": topic,
        "joke": "",
        "rating": "",
        "feedback": "",
        "joke_history":[],
        "attempt_count":0
    }
    
    print(f"\n🎬 Generating joke about '{topic}'...\n")
    
    # Stream the process
    # Stream returns a dictionary with node names as keys
    config = {"configurable": {"thread_id": "joke_session_001"}}
    for chunk in app.stream(initial_state, config):      
        for node_name, state_update in chunk.items():
            print(f"\n📍 Node executed: {node_name}")
            if state_update:
                for key, value in state_update.items():
                    if value:  # Only print non-empty values
                        print(f"   {key}: {str(value)[:100]}...")
    
    # Final result
    result = app.invoke(initial_state,config)
    
    print("\n" + "="*50)
    print("🎉 FINAL JOKE:")
    print("="*50)
    print(result["joke"])
    print(f"\nRating: {result['rating']}")
