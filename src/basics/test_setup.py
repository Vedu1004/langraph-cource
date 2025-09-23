import os
from dotenv import load_dotenv

load_dotenv()


def testimports():
    try:
        import langchain
        print(f"langchain version : {langchain.__version__}")

        # import langgraph
        # print(f"langraph :{langgraph.__version__}")

        api_key = os.getenv("OPENAI_API_KEY")

        if api_key:
            print("have the key")
        else:
            print("no key")

        return True
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    

if __name__ == "__main__":
    print('langraph learning env')

    if testimports():
        print("\n📦 All packages imported successfully!")
        
        print("\n🤖 Testing LLM connection...")